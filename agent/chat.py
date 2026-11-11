"""Chat v2: ngobrol dengan agen seperti AI biasa.

Cara pakai (di Codespace):
    python -m agent.chat

Lalu ketik perintah seperti chat biasa, contoh:
    Kamu: cek https://website-kamu.example
    Kamu: lanjut scan SQL-nya
    Kamu: itu salah, seharusnya lanjut ke form laporan
    Kamu: /pelajaran
    Kamu: exit

Bukan lagi: python -m agent.main "prompt" sekali jalan lalu mati.

Agen membaca agent/lessons.md sebelum setiap tugas, menyimpan
riwayat di .agent_memory.json (lokal, tidak di-commit), dan
mencatat kesalahan baru sebagai pelajaran.
"""
import sys

from .agent import run
from .memory import add_lesson, load_history, load_lessons, save_history


def summarize(trace):
    lines = []
    for step in trace:
        if not step["ok"]:
            lines.append(f"- Tool {step['tool']} gagal: {step.get('error')}")
            continue
        r = step["result"]
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


def main():
    lessons = load_lessons()
    history = load_history()
    print("=== lion-cyber-agent — chat ===")
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
                "  cari CVE terbaru untuk XSS\n"
                "  /pelajaran — lihat pelajaran dari kesalahan\n"
                "  Kalau saya salah, tulis 'itu salah' lalu saya tanya perbaikannya."
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
        lessons_now = load_lessons()
        print(f"Agen: Saya cek dulu {len(lessons_now)} pelajaran saya, lalu jalankan tugasnya...")
        trace = run(text)
        print("Agen:")
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
        history.append({"role": "assistant", "content": summarize(trace)})
        save_history(history)


if __name__ == "__main__":
    sys.exit(main())
