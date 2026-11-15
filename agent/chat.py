"""Chat v3: ngobrol dengan agen seperti AI biasa — sekarang dengan otak Gemini.

Cara pakai (di Codespace):
    python -m agent.chat                       # auto: Gemini kalau ada key, kalau tidak rule-based
    python -m agent.chat --brain local         # otak lokal Kumar (adapter LoRA hasil fine-tune)
    python -m agent.chat --brain rule          # selalu rule-based v2
    python -m agent.chat --brain gemini        # selalu coba Gemini dulu

Otak lokal butuh folder adapter hasil Colab (kumar-lora-trial) di root
repo + pip install torch transformers peft accelerate. Lihat
docs/otak-lokal.md. Kalau otak lokal tidak tersedia atau keputusannya
tidak valid, chat jatuh ke mode rule-based v2 (tidak pernah crash).

Lalu ketik perintah seperti chat biasa, contoh:
    Kamu: cek https://website-kamu.example
    Kamu: lanjut scan SQL-nya
    Kamu: itu salah, seharusnya lanjut ke form laporan
    Kamu: /pelajaran
    Kamu: exit

Bukan lagi: python -m agent.main "prompt" sekali jalan lalu mati.

Otak: kalau GEMINI_API_KEY ada di .env, chat memakai Gemini
(agent/brain.py) untuk memahami perintah. Kalau tidak ada,
fallback ke mode rule-based v2. Validator (agent/validator.py)
yang memutuskan apakah sebuah tool boleh dijalankan — model
hanya menyarankan, kode yang menegakkan aturan Lion.

Agen membaca agent/lessons.md sebelum setiap tugas, menyimpan
riwayat di .agent_memory.json (lokal, tidak di-commit), dan
mencatat kesalahan baru sebagai pelajaran.
"""
import argparse
import os
import sys

from .agent import TOOLS, extract_url, is_sql_scan, run
from .brain import ask_gemini, has_api_key
from .local_brain import DEFAULT_ADAPTER_DIR, LocalBrainError, load_local_brain
from .memory import add_lesson, load_history, load_lessons, save_history
from .validator import validate_tool_call


def summarize(trace):
    lines = []
    for step in trace:
        if not step["ok"]:
            lines.append(f"- Tool {step['tool']} gagal: {step.get('error')}")
            continue
        r = step["result"]
        if step["tool"] == "scan_sql" and isinstance(r, dict):
            lines.append(
                f"- scan_sql: {r.get('url')} param={r.get('param')} "
                f"(baseline status {r.get('baseline_status')})"
            )
            findings = r.get("findings") or []
            if not findings:
                lines.append(
                    "  * Tidak ada sinyal kuat. Bukan berarti 100% aman — lanjutkan audit kode."
                )
            for f in findings:
                lines.append(
                    f"  * payload {f.get('payload')!r}: status {f.get('status')}, "
                    f"kemiripan {f.get('similarity_to_baseline')}, "
                    f"tanda error DB: {f.get('db_error_signs') or '-'}"
                )
                if f.get("note"):
                    lines.append(f"    {f['note']}")
            continue
        if step["tool"] == "entry_rank" and isinstance(r, dict):
            # Hasil entry_rank TIDAK punya field 'status' — cabang umum
            # di bawah (title + status) mencetak "(status None)" dan
            # menghilangkan angka peringkatnya (bukti: uji v8 soal 2,
            # 2026-11-15). Tampilkan peringkatnya secara eksplisit.
            rank = r.get("rank")
            if isinstance(rank, int):
                lines.append(
                    f"- entry_rank: peringkat {rank} dari {r.get('total_entries')} "
                    f"(zona hadiah: {'ya' if r.get('in_prize_zone') else 'tidak'})"
                )
            else:
                lines.append("- entry_rank: entry ditemukan tapi belum ada peringkat")
            lines.append(f"  * Entry: {r.get('title')}")
            if r.get("matches") is not None:
                lines.append(
                    f"  * Rekor juri: {r.get('wins')} menang / {r.get('draws')} seri / "
                    f"{r.get('losses')} kalah dari {r.get('matches')} pertandingan"
                )
            if r.get("prize_rank") is not None:
                lines.append(f"  * Peringkat hadiah: {r.get('prize_rank')}")
            continue
        if step["tool"] == "find_password_entry" and isinstance(r, dict):
            lines.append(f"- find_password_entry: {r.get('summary')}")
            for inp in r.get("password_inputs") or []:
                if inp.get("source", "").startswith("script"):
                    lines.append(
                        f"  * Kolom password dibuat lewat JavaScript ({inp.get('script', 'script inline')}): {inp.get('note', '')}"
                    )
                else:
                    lines.append(
                        f"  * Kolom <input type=\"password\"> field '{inp.get('field_name')}' "
                        f"di form {inp.get('form_action') or '(halaman yang sama)'} "
                        f"({inp.get('form_method') or 'GET'})"
                    )
            for p in r.get("password_prompts") or []:
                detail = f"prompt \"{p.get('prompt_text')}\""
                if p.get("method"):
                    detail += f" — menjaga {p['method']}"
                    if p.get("endpoint"):
                        detail += f" {p['endpoint']}"
                if p.get("headers"):
                    detail += f" (header: {', '.join(p['headers'])})"
                lines.append(f"  * Dialog JS: {detail}")
            for b in r.get("password_buttons") or []:
                lines.append(f"  * Tombol/link: \"{b.get('text')}\" ({b.get('tag')})")
            continue
        if step["tool"] == "try_admin_password" and isinstance(r, dict):
            if r.get("accepted"):
                lines.append(
                    f"- try_admin_password: password admin diterima: '{r.get('password')}' "
                    f"(setelah {r.get('attempts')} percobaan)"
                )
                lines.append("  * Password ini LEMAH — ganti setelah tes.")
            else:
                lines.append(
                    f"- try_admin_password: tidak ada yang diterima setelah "
                    f"{r.get('attempts')} percobaan"
                )
            lines.append(f"  * {r.get('message')}")
            if r.get("changed") is False:
                lines.append("  * Tidak ada data yang berubah.")
            continue
        if isinstance(r, dict) and "findings" in r:
            lines.append(f"- {step['tool']}: status {r.get('status')}")
            for f in r["findings"]:
                lines.append(f"  * {f}")
        elif isinstance(r, dict) and "title" in r:
            lines.append(f"- {step['tool']}: {r.get('title')} (status {r.get('status')})")
        elif isinstance(r, list):
            for item in r[:5]:
                lines.append(f"  * {item.get('title', item)} — {item.get('url', '')}")
        else:
            lines.append(f"- {step['tool']}: selesai")
    return "\n".join(lines) if lines else "Tidak ada hasil."


def handle_feedback(text, history):
    """User mengoreksi agen. Simpan sebagai pelajaran."""
    print("Agen: Oke, saya catat. Apa yang seharusnya saya lakukan?")
    fix = input("Perbaikan: ").strip()
    if fix:
        add_lesson(mistake=text, fix=fix)
        print("Agen: Sudah saya simpan di agent/lessons.md. Lain kali saya tidak ulangi.")
    else:
        print("Agen: Oke, tidak jadi dicatat.")
    history.append({"role": "user", "content": text})
    history.append({"role": "assistant", "content": "Mencatat pelajaran baru."})
    save_history(history)


def execute_brain_tool(tool_call, last_url=None):
    """Jalankan tool yang diminta Gemini, setelah divalidasi.

    Kembalikan (trace_step, new_last_url). Validator yang memutuskan —
    kalau ditolak, tool tidak dijalankan sama sekali.
    """
    name = tool_call.get("tool", "")
    args = tool_call.get("args", {}) or {}
    # "lanjut scan SQL" tanpa URL: pakai URL terakhir.
    if name == "scan_sql" and not args.get("url") and last_url:
        args = dict(args, url=last_url)
    ok, reason = validate_tool_call(name, args)
    if not ok:
        return {"tool": name, "kwargs": args, "ok": False, "error": f"Validator menolak: {reason}"}, last_url
    fn = TOOLS.get(name)
    if fn is None:
        return {"tool": name, "kwargs": args, "ok": False, "error": f"Tool '{name}' tidak dikenal."}, last_url
    try:
        result = fn(**args)
        new_url = args.get("url") or last_url
        return {"tool": name, "kwargs": args, "ok": True, "result": result}, new_url
    except Exception as e:  # noqa: BLE001
        return {"tool": name, "kwargs": args, "ok": False, "error": str(e)}, last_url


def main():
    parser = argparse.ArgumentParser(description="Chat dengan lion-cyber-agent.")
    parser.add_argument(
        "--brain",
        choices=["auto", "rule", "gemini", "local"],
        default="auto",
        help="Otak yang dipakai: auto (Gemini kalau ada key, kalau tidak rule-based), "
        "rule (selalu rule-based v2), gemini (selalu coba Gemini dulu), "
        "local (adapter LoRA Kumar, fallback ke rule-based kalau tidak tersedia).",
    )
    parser.add_argument(
        "--adapter",
        default=DEFAULT_ADAPTER_DIR,
        help="Folder adapter LoRA untuk --brain local (default: ./kumar-lora-trial).",
    )
    args = parser.parse_args()
    brain_mode = args.brain
    local_brain = None
    local_brain_failed = False

    lessons = load_lessons()
    history = load_history()
    last_url = None  # URL terakhir yang dicek — dipakai "lanjut ..." berikutnya.
    for entry in reversed(history):
        if entry.get("role") == "user":
            last_url = extract_url(entry.get("content", ""))
            if last_url:
                break
    print("=== lion-cyber-agent — chat ===")
    print(f"Otak: {brain_mode}" + (f" (adapter: {args.adapter})" if brain_mode == "local" else ""))
    if brain_mode == "local" and not os.path.isdir(args.adapter):
        print(
            "Peringatan: folder adapter tidak ditemukan — "
            "otak lokal akan fallback ke rule-based. "
            "Upload/unzip folder kumar-lora-trial ke root repo dulu."
        )
    print("Ketik perintah seperti ngobrol biasa. Ketik /bantuan, /pelajaran, atau exit.")
    if lessons:
        print(f"\nSaya ingat {len(lessons)} pelajaran dari kesalahan sebelumnya.")
    print()

    while True:
        try:
            text = input("Kamu: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAgen: Sampai jumpa.")
            break
        if not text:
            continue
        if text.lower() in ("exit", "quit", "keluar"):
            save_history(history)
            print("Agen: Sampai jumpa. Riwayat tersimpan.")
            break
        if text.lower() in ("/bantuan", "bantuan", "/help"):
            print(
                "Agen: Contoh perintah:\n"
                "  cek https://website-kamu.example\n"
                "  lanjut scan SQL-nya (pakai website yang terakhir dicek)\n"
                "  scan SQL https://website-kamu.example param username\n"
                "  cari CVE terbaru untuk XSS\n"
                "  /pelajaran — lihat pelajaran dari kesalahan\n"
                "  Kalau saya salah, tulis 'itu salah' lalu saya tanya perbaikannya.\n"
                "  Otak Gemini aktif kalau GEMINI_API_KEY ada di .env, "
                "kalau tidak ada saya pakai mode rule-based v2.\n"
                "  Otak lokal Kumar: jalankan python -m agent.chat --brain local "
                "(butuh folder adapter kumar-lora-trial di root repo, "
                "lihat docs/otak-lokal.md)."
            )
            continue
        if text.lower() in ("/pelajaran", "pelajaran"):
            print("Agen: Pelajaran saya:")
            for i, lesson in enumerate(load_lessons(), 1):
                print(f"  {i}. {lesson}")
            continue
        if "salah" in text.lower() or "itu keliru" in text.lower():
            handle_feedback(text, history)
            continue

        # Tugas biasa: baca pelajaran dulu, lalu jalankan tools.
        # "Lanjut scan SQL" tanpa URL yang pernah dicek: tanya dulu,
        # jangan cari tutorial di web (pelajaran 6).
        if is_sql_scan(text) and not extract_url(text) and not last_url:
            print(
                "Agen: Website mana yang mau saya scan SQL-nya? "
                "Tulis URL-nya, contoh: scan SQL https://website-kamu.example param username"
            )
            continue
        lessons_now = load_lessons()
        print(f"Agen: Saya cek dulu {len(lessons_now)} pelajaran saya, lalu jalankan tugasnya...")
        # --- Otak lokal Kumar (v5): adapter LoRA hasil fine-tune ---
        trace = None
        reply_text = ""
        if brain_mode == "local" and not local_brain_failed:
            if local_brain is None:
                try:
                    print("Agen: Memuat otak lokal Kumar (adapter LoRA)...")
                    local_brain = load_local_brain(adapter_dir=args.adapter)
                    print("Agen: Otak lokal Kumar aktif.")
                except LocalBrainError as e:
                    print(f"Agen: Otak lokal tidak tersedia ({e}) Saya pakai mode rule-based.")
                    local_brain_failed = True
            if local_brain is not None:
                kind, *rest = local_brain.decide(text, last_url=last_url)
                if kind == "tool":
                    name, tool_args = rest
                    step, last_url = execute_brain_tool(
                        {"tool": name, "args": tool_args}, last_url=last_url
                    )
                    trace = [step]
                    reply_text = local_brain.answer_with_context(
                        text, step.get("result") or step.get("error")
                    )
                elif kind == "answer":
                    reply_text = rest[0]
                else:
                    print(
                        f"Agen: Otak lokal belum yakin ({rest[0]}), "
                        "saya pakai mode rule-based."
                    )
        # --- Otak Gemini (v3) kalau API key ada ---
        if trace is None and not reply_text and brain_mode in ("auto", "gemini") and has_api_key():
            print("Agen: Otak Gemini aktif, saya tanya dulu ke Gemini...")
            brain = ask_gemini(text, lessons_now, history, last_url=last_url)
            if brain.get("error"):
                print(f"Agen: Gemini gagal ({brain['error']}), saya pakai mode rule-based v2.")
            elif brain.get("tool_call"):
                step, last_url = execute_brain_tool(brain["tool_call"], last_url=last_url)
                trace = [step]
                # Minta Gemini merangkum hasil tool, kalau gagal pakai ringkasan lokal.
                summary_ctx = f"Hasil tool {step['tool']}: {step.get('result') or step.get('error')}"
                brain2 = ask_gemini(
                    f"Rangkum hasil ini untuk user dalam bahasa Indonesia: {summary_ctx}",
                    lessons_now,
                    history,
                    last_url=last_url,
                )
                if brain2.get("reply"):
                    reply_text = brain2["reply"]
            elif brain.get("reply"):
                reply_text = brain["reply"]
        # --- Fallback rule-based v2 ---
        if trace is None and not reply_text:
            trace = run(text, last_url=last_url)
        trace = trace or []
        for step in trace:
            if step["ok"] and isinstance(step.get("result"), dict) and step["result"].get("url"):
                last_url = step["result"]["url"]
        if extract_url(text):
            last_url = extract_url(text)
        print("Agen:")
        if reply_text:
            print(reply_text)
        if trace:
            print(summarize(trace))
        # Pelajaran otomatis dari kegagalan tool
        for step in trace:
            if not step["ok"]:
                add_lesson(
                    mistake=f"Tool {step['tool']} gagal: {step.get('error')}",
                    fix="Coba cara lain sekali, jangan ulang cara yang sama persis.",
                )
        print("\nAgen: Kalau ada yang salah dari jawaban saya, tulis saja 'itu salah'.")
        history.append({"role": "user", "content": text})
        history.append(
            {"role": "assistant", "content": reply_text or summarize(trace)}
        )
        save_history(history)


if __name__ == "__main__":
    sys.exit(main())
