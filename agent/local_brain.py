"""Otak lokal Kumar (v5) — adapter LoRA hasil fine-tune sebagai otak agen.

Ini yang menggabungkan otak dan badan: adapter hasil latih di Colab
(base Qwen2.5-Coder-0.5B + adapter LoRA) dipakai untuk memutuskan
tool apa yang harus dijalankan, lalu agent/chat.py menjalankan tool
itu lewat validator seperti biasa.

Pola muat modelnya SAMA PERSIS dengan training/run_kumar.py yang
sudah terbukti jalan di laptop Lion (greedy + repetition_penalty 1.15,
float16 di CUDA, float32 di CPU).

Yang penting:
- Model hanya MENYARANKAN. Validator (agent/validator.py) yang
  memutuskan apakah tool boleh jalan — sama seperti otak Gemini.
  Keputusan yang tidak lolos validator = GAGAL secara terlihat.
  Tidak ada penyelamatan otomatis ke rule-based (dihapus 2026-11-16
  atas perintah Lion — supaya kemampuan otak terlihat apa adanya).
- Adapter hasil latih percobaan (37 contoh) BELUM dilatih memanggil
  tool dengan andal — ia akan sering gagal secara terlihat sampai
  fine-tune berikutnya yang memakai contoh tool-calling di dataset/.
- torch / transformers / peft diimpor LAZY di dalam load(), supaya
  modul ini tetap bisa diimpor di mesin yang belum memasang
  pustaka itu (misalnya saat cek impor di lab).
"""

import json
import os
import re
from pathlib import Path

from .agent import (
    DEFAULT_HANDLE,
    TOOLS,
    extract_handle,
    extract_slug,
    extract_submission_id,
    extract_url,
    is_admin_password,
    is_github_tool,
    is_makefun,
    is_password_entry,
    is_rank_query,
    is_sql_scan,
)
from .validator import validate_tool_call

BASE_MODEL = "Qwen/Qwen2.5-Coder-0.5B"
DEFAULT_ADAPTER_DIR = "./kumar-lora-trial"

# System prompt yang dipakai decide() dan answer_with_context().
# HARUS sama persis dengan SYSTEM di training/kumar-trial-train.ipynb —
# adapter hanya pernah melihat prompt ini saat latih. Prompt yang lebih
# panjang (mis. system_prompt.md + daftar tool + instruksi JSON) TIDAK
# PERNAH dilihat adapter saat latih, jadi ia tidak meresponsnya dengan
# benar — buktinya v2 tetap mengulang rambel v1 dan salah pilih tool.
TRAINING_SYSTEM_PROMPT = "Kamu adalah Kumar, asisten AI keamanan siber dan coding milik Lion. Jawablah dengan singkat dan benar."

# Argumen wajib per tool — kalau tidak ada, keputusan dianggap
# tidak lengkap dan GAGAL secara terlihat (bukan ditebak-tebak,
# bukan penyelamatan ke rule-based).
REQUIRED_ARGS = {
    "check_site_basic": ("url",),
    "fetch_url": ("url",),
    "scan_sql": ("url",),
    "find_password_entry": ("url",),
    "competition_status": ("slug",),
    "my_entry_status": ("submission_id",),
    "vet_tool": ("repo_full_name",),
    "read_repo_file": ("owner", "repo", "path"),
}

# TIDAK ADA alias nama tool (dihapus 2026-11-16 atas perintah Lion).
# Otak harus mengeluarkan nama tool yang PERSIS (check_site_basic,
# scan_sql, entry_rank, try_admin_password, ...) atau gagal secara
# terlihat — alias menutupi nama yang salah dari otak, dan itu bagian
# dari masalah penyelamatan itu.


class LocalBrainError(Exception):
    """Otak lokal tidak bisa dipakai (adapter hilang / pustaka belum terpasang)."""


def parse_tool_call(text):
    """Cari satu JSON tool-call di dalam teks model.

    Kembalikan dict {"tool": ..., "args": {...}} atau None kalau
    tidak ada JSON tool-call yang utuh. Teks di sekitar JSON
    (misalnya penjelasan singkat) diabaikan — yang dicari JSON-nya.
    """
    if not text:
        return None
    stripped = text.strip()
    # Coba seluruh teks dulu (kasus ideal: model menjawab hanya JSON).
    try:
        parsed = json.loads(stripped)
        if isinstance(parsed, dict) and "tool" in parsed:
            return parsed
    except Exception:
        pass
    # Cari objek JSON pertama yang mengandung "tool".
    decoder = json.JSONDecoder()
    for match in re.finditer(r"\{", stripped):
        try:
            parsed, _ = decoder.raw_decode(stripped[match.start():])
        except Exception:
            continue
        if isinstance(parsed, dict) and "tool" in parsed:
            return parsed
    # Terakhir: coba tiap baris.
    for line in stripped.splitlines():
        line = line.strip()
        if line.startswith("{") and '"tool"' in line:
            try:
                parsed = json.loads(line)
            except Exception:
                continue
            if isinstance(parsed, dict) and "tool" in parsed:
                return parsed
    return None


def _find_adapter_dir(adapter_dir):
    """Cari folder adapter. Mendukung layout flat (file adapter
    langsung di folder kerja, tanpa subfolder kumar-lora-trial) —
    sama seperti training/run_kumar.py."""
    path = Path(adapter_dir)
    if (path / "adapter_config.json").exists():
        return path
    # Default + file adapter ada langsung di folder kerja.
    if path == Path(DEFAULT_ADAPTER_DIR) and (Path.cwd() / "adapter_config.json").exists():
        return Path.cwd()
    return path


class LocalBrain:
    """Otak lokal: base model + adapter LoRA Kumar."""

    def __init__(self, adapter_dir=DEFAULT_ADAPTER_DIR, base=BASE_MODEL):
        self.adapter_dir = _find_adapter_dir(adapter_dir)
        self.base = base
        self.tok = None
        self.model = None
        self.device = "cpu"

    def load(self):
        """Muat tokenizer + base + adapter. Lempar LocalBrainError
        dengan pesan yang bisa ditindaklanjuti kalau gagal."""
        if not (self.adapter_dir / "adapter_config.json").exists():
            raise LocalBrainError(
                f"Folder adapter tidak ditemukan di {self.adapter_dir}. "
                "Upload/unzip folder kumar-lora-trial hasil Colab ke root repo "
                "(di Codespace: drag-drop foldernya ke file explorer), "
                "lalu jalankan lagi."
            )
        try:
            import torch
            from peft import PeftModel
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as e:
            raise LocalBrainError(
                "Pustaka model belum terpasang "
                f"({e}). Jalankan: pip install torch transformers peft accelerate"
            ) from e
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        dtype = torch.float16 if self.device == "cuda" else torch.float32
        self.tok = AutoTokenizer.from_pretrained(self.base)
        base_model = AutoModelForCausalLM.from_pretrained(
            self.base,
            torch_dtype=dtype,
            device_map="auto" if self.device == "cuda" else None,
            attn_implementation="sdpa",
        )
        if self.device == "cpu":
            base_model = base_model.to("cpu")
        self.model = PeftModel.from_pretrained(base_model, str(self.adapter_dir))
        self.model.eval()
        return self

    def _generate(self, messages, max_new_tokens=256):
        """Generate satu jawaban dari adapter (greedy + repetition_penalty,
        pola yang sama seperti training/run_kumar.py)."""
        text = self.tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        ids = self.tok(text, return_tensors="pt").to(self.model.device)
        # Berhenti di <|im_end|>: format latih mengakhiri SETIAP jawaban
        # assistant dengan token itu, tapi eos bawaan model adalah
        # <|endoftext|>. Tanpa ini generate() terus jalan sampai
        # max_new_tokens dan model mengisi sisanya dengan <|fim_pad|>.
        # Perbaikan 2026-11-15 (banjir fim_pad di uji v6): <|fim_pad|>
        # TIDAK ditandai special di tokenizer Qwen2.5-Coder
        # (tokenizer_config.json: "special": false, id 151662), jadi
        # decode(skip_special_tokens=True) TIDAK membuangnya. Karena
        # itu fim_pad juga dimasukkan ke eos (generate berhenti saat
        # model mengeluarkan pad pertama) DAN teks hasil decode
        # dipotong manual di kemunculan pertama <|fim_pad|>.
        # Perbaikan 2026-11-16 (bocor di uji v10 PC Lion): <|fim_suffix|>
        # (id 151661) dan <|fim_middle|> (id 151660) juga TIDAK special
        # dan ikut bocor ke output — perlakuannya sama: masuk eos + potong.
        im_end_id = self.tok.convert_tokens_to_ids("<|im_end|>")
        fim_pad_id = self.tok.convert_tokens_to_ids("<|fim_pad|>")
        fim_suffix_id = self.tok.convert_tokens_to_ids("<|fim_suffix|>")
        fim_middle_id = self.tok.convert_tokens_to_ids("<|fim_middle|>")
        eos_ids = [self.tok.eos_token_id]
        for extra in (im_end_id, fim_pad_id, fim_suffix_id, fim_middle_id):
            if extra is not None and extra not in eos_ids:
                eos_ids.append(extra)
        out = self.model.generate(
            **ids,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            repetition_penalty=1.15,
            pad_token_id=self.tok.eos_token_id,
            eos_token_id=eos_ids,
        )
        text = self.tok.decode(out[0][ids["input_ids"].shape[1]:], skip_special_tokens=True)
        for marker in ("<|fim_pad|>", "<|im_end|>", "<|fim_suffix|>", "<|fim_middle|>"):
            if marker in text:
                text = text.split(marker, 1)[0]
        return text

    def decide(self, task, last_url=None):
        """Putuskan: jalankan tool, jawab langsung, atau GAGAL secara terlihat.

        Kembalikan ("tool", nama, args) / ("answer", teks) /
        ("failed", alasan, output_mentah). "failed" berarti otak gagal —
        chat.py TIDAK BOLEH menjalankan plan rule-based; kegagalan
        ditampilkan apa adanya (alasan + output mentah otak) dan dicatat
        sebagai pelajaran.
        """
        # Format prompt SAMA PERSIS seperti saat latih (lihat
        # training/kumar-trial-train.ipynb: format_row): system prompt
        # pendek yang tetap + user = instruction + input. Adapter TIDAK
        # pernah melihat daftar tool atau instruksi JSON saat latih —
        # nama-nama tool ia pelajari dari contoh-contoh tool-calling
        # di dataset. Validator tetap yang menegakkan keamanan.
        user = task.strip()
        # Baris URL terakhir HANYA ditambahkan bila tugas ini memang
        # butuh URL (lanjutan/cek/scan tanpa URL sendiri). Kalau
        # ditambahkan ke SEMUA tugas, adapter terpaku pada URL itu
        # bahkan saat tugasnya tidak berhubungan — bukti: ujian v6/v7
        # soal 2, ditanya peringkat malah cek verifydeal lagi. Isi
        # last_url untuk tool tanpa URL tetap diisi di bawah (kode),
        # jadi baris ini tidak perlu ada di prompt untuk tugas lain.
        if last_url and not extract_url(task):
            t = task.lower()
            is_rank = any(k in t for k in ("peringkat", "rank", "posisi", "ranking"))
            is_continuation = any(
                k in t for k in ("lanjut", "scan", "cek", "periksa", "uji", "test")
            )
            # JANGAN tempel last_url ke tugas coba password admin:
            # password ini khusus verifydeal.site, sedangkan last_url
            # bisa situs lain (mis. demo.owasp-juice.shop dari cek
            # sebelumnya) — model bisa salah mencoba password ke sana.
            if is_continuation and not is_rank and not is_admin_password(task):
                user += f"\n\nURL terakhir yang dicek: {last_url}"
        messages = [
            {"role": "system", "content": TRAINING_SYSTEM_PROMPT},
            {"role": "user", "content": user},
        ]
        try:
            raw = self._generate(messages)
        except Exception as e:  # noqa: BLE001 - model gagal = gagal terlihat
            return ("failed", f"otak lokal gagal menjawab: {e}", "")
        parsed = parse_tool_call(raw)
        if parsed is not None:
            # Nama tool dipakai APA ADANYA — tidak ada alias (dihapus
            # 2026-11-16). Nama yang salah = gagal secara terlihat.
            name = str(parsed.get("tool", ""))
            args = parsed.get("args") or {}
            if not isinstance(args, dict):
                return ("failed", "args tool-call bukan objek JSON", raw)
            if name not in TOOLS:
                return ("failed", f"tool '{name}' tidak dikenal", raw)
            # "Lanjut ..." tanpa URL: pakai URL terakhir.
            if (
                name in ("scan_sql", "check_site_basic", "fetch_url", "find_password_entry")
                and not args.get("url")
                and last_url
            ):
                args = dict(args, url=last_url)
            # entry_rank boleh tanpa slug kalau ada submission id / handle.
            if name == "entry_rank" and not (args.get("slug") or args.get("submission_id") or args.get("handle")):
                return ("failed", "entry_rank butuh slug, submission id, atau handle", raw)
            # "Peringkat saya" tanpa handle/id: pakai handle Lion, kalau
            # tidak entry_rank gagal di tool-nya (bukti: uji v7 soal 2).
            if name == "entry_rank" and not args.get("submission_id") and not args.get("handle"):
                args = dict(args, handle=DEFAULT_HANDLE)
            missing = [k for k in REQUIRED_ARGS.get(name, ()) if not args.get(k)]
            if missing:
                return ("failed", f"tool '{name}' kekurangan argumen: {', '.join(missing)}", raw)
            ok, reason = validate_tool_call(name, args)
            if not ok:
                return ("failed", f"validator menolak: {reason}", raw)
            return ("tool", name, args)
        # Jawaban teks biasa — tapi kalau tugas ini jelas-jelas sebuah
        # AKSI (cek / scan / cari / baca / peringkat), jangan biarkan
        # model menjawab dari ingatan: GAGAL secara terlihat (bukan penyelamatan).
        # Pertanyaan konsep ("jelaskan apa itu SQL injection",
        # "cari tahu apa itu XSS") BUKAN aksi — boleh dijawab langsung.
        t = task.lower()
        needs_tool = bool(extract_url(task))
        if is_sql_scan(task) and any(k in t for k in ("scan", "cek", "uji", "lanjut", "test")):
            needs_tool = True
        if is_rank_query(task) and (
            extract_slug(task)
            or extract_submission_id(task)
            or extract_handle(task)
            or any(k in t for k in ("cek", "lihat", "berapa"))
        ):
            needs_tool = True
        if is_makefun(task) and any(
            k in t for k in ("cek", "bounty", "kompetisi", "entry", "submission", "buka")
        ):
            needs_tool = True
        if is_github_tool(task):
            needs_tool = True
        if is_password_entry(task):
            needs_tool = True
        if is_admin_password(task):
            needs_tool = True
        if any(k in t for k in ("cek ", "scan ", "periksa ", "baca ")):
            needs_tool = True
        if "cari " in t and "cari tahu" not in t and "cari tau" not in t:
            needs_tool = True
        if needs_tool:
            return ("failed", "otak lokal menjawab teks padahal tugas ini butuh tool", raw)
        return ("answer", raw.strip())

    def answer_with_context(self, task, tool_result):
        """Minta adapter merangkum hasil tool jadi jawaban singkat
        bahasa Indonesia. Kembalikan ringkasan MENTAH apa adanya
        (walau berantakan — guard yang membuangnya dihapus 2026-11-16
        atas perintah Lion, supaya Lion melihat yang sebenarnya).
        Kembalikan "" hanya kalau generate gagal."""
        # Bentuk user SAMA seperti baris "merangkum hasil tool" di dataset
        # (mis. baris 52-53): instruction singkat + input "Hasil tool: ...".
        user = (
            "Rangkum hasil pengecekan ini untuk user dalam bahasa Indonesia.\n"
            f"Hasil tool: {str(tool_result)[:2000]}"
        )
        try:
            text = self._generate(
                [
                    {"role": "system", "content": TRAINING_SYSTEM_PROMPT},
                    {"role": "user", "content": user},
                ]
            ).strip()
        except Exception:  # noqa: BLE001 - generate gagal = tidak ada ringkasan
            return ""
        # TIDAK ADA guard lagi (dihapus 2026-11-16): ringkasan mentah
        # otak dikembalikan apa adanya, walau menggemakan JSON,
        # berantakan, atau berulang — supaya Lion melihat kemampuan
        # otak yang sebenarnya.
        return text


def load_local_brain(adapter_dir=DEFAULT_ADAPTER_DIR, base=BASE_MODEL):
    """Muat otak lokal dan kembalikan LocalBrain yang sudah siap."""
    return LocalBrain(adapter_dir=adapter_dir, base=base).load()
