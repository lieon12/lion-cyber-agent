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
  Keputusan yang tidak lolos validator = fallback ke rule-based.
- Adapter hasil latih percobaan (37 contoh) BELUM dilatih memanggil
  tool dengan andal — ia akan sering fallback sampai fine-tune
  berikutnya yang memakai contoh tool-calling di dataset/.
- torch / transformers / peft diimpor LAZY di dalam load(), supaya
  modul ini tetap bisa diimpor di mesin yang belum memasang
  pustaka itu (misalnya saat cek impor di lab).
"""

import json
import os
import re
from pathlib import Path

from .agent import (
    TOOLS,
    extract_handle,
    extract_slug,
    extract_submission_id,
    extract_url,
    is_github_tool,
    is_makefun,
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
# tidak lengkap dan jatuh ke fallback (bukan ditebak-tebak).
REQUIRED_ARGS = {
    "check_site_basic": ("url",),
    "fetch_url": ("url",),
    "scan_sql": ("url",),
    "competition_status": ("slug",),
    "my_entry_status": ("submission_id",),
    "vet_tool": ("repo_full_name",),
    "read_repo_file": ("owner", "repo", "path"),
}

# Nama lama di system_prompt.md, plus nama karangan yang mungkin
# dihasilkan model (bukti nyata: uji v3 memanggil 'check_url'
# padahal maksudnya check_site_basic) — dinormalisasi ke nama
# yang benar-benar dipanggil agen. Validator tetap yang
# memutuskan apakah tool boleh jalan.
_TOOL_ALIASES = {
    "sql_scan": "scan_sql",
    "check_url": "check_site_basic",
    "check_site": "check_site_basic",
    "check_website": "check_site_basic",
    "sql_injection_scan": "scan_sql",
    "check_sql": "scan_sql",
    "get_url": "fetch_url",
    "fetch": "fetch_url",
    "search": "search_web",
    "get_rank": "entry_rank",
    "check_rank": "entry_rank",
}


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
        out = self.model.generate(
            **ids,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            repetition_penalty=1.15,
            pad_token_id=self.tok.eos_token_id,
        )
        return self.tok.decode(out[0][ids["input_ids"].shape[1]:], skip_special_tokens=True)

    def decide(self, task, last_url=None):
        """Putuskan: jalankan tool, jawab langsung, atau fallback.

        Kembalikan ("tool", nama, args) / ("answer", teks) /
        ("fallback", alasan). Fallback berarti chat.py harus memakai
        mode rule-based untuk tugas ini.
        """
        # Format prompt SAMA PERSIS seperti saat latih (lihat
        # training/kumar-trial-train.ipynb: format_row): system prompt
        # pendek yang tetap + user = instruction + input. Adapter TIDAK
        # pernah melihat daftar tool atau instruksi JSON saat latih —
        # nama-nama tool ia pelajari dari contoh-contoh tool-calling
        # di dataset. Validator tetap yang menegakkan keamanan.
        user = task.strip()
        if last_url:
            user += f"\n\nURL terakhir yang dicek: {last_url}"
        messages = [
            {"role": "system", "content": TRAINING_SYSTEM_PROMPT},
            {"role": "user", "content": user},
        ]
        try:
            raw = self._generate(messages)
        except Exception as e:  # noqa: BLE001 - model gagal = fallback
            return ("fallback", f"otak lokal gagal menjawab: {e}")
        parsed = parse_tool_call(raw)
        if parsed is not None:
            name = _TOOL_ALIASES.get(str(parsed.get("tool", "")), str(parsed.get("tool", "")))
            args = parsed.get("args") or {}
            if not isinstance(args, dict):
                return ("fallback", "args tool-call bukan objek JSON")
            if name not in TOOLS:
                return ("fallback", f"tool '{name}' tidak dikenal")
            # "Lanjut ..." tanpa URL: pakai URL terakhir.
            if name in ("scan_sql", "check_site_basic", "fetch_url") and not args.get("url") and last_url:
                args = dict(args, url=last_url)
            # entry_rank boleh tanpa slug kalau ada submission id / handle.
            if name == "entry_rank" and not (args.get("slug") or args.get("submission_id") or args.get("handle")):
                return ("fallback", "entry_rank butuh slug, submission id, atau handle")
            missing = [k for k in REQUIRED_ARGS.get(name, ()) if not args.get(k)]
            if missing:
                return ("fallback", f"tool '{name}' kekurangan argumen: {', '.join(missing)}")
            ok, reason = validate_tool_call(name, args)
            if not ok:
                return ("fallback", f"validator menolak: {reason}")
            return ("tool", name, args)
        # Jawaban teks biasa — tapi kalau tugas ini jelas-jelas sebuah
        # AKSI (cek / scan / cari / baca / peringkat), jangan biarkan
        # model menjawab dari ingatan: fallback ke rule-based.
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
        if any(k in t for k in ("cek ", "scan ", "periksa ", "baca ")):
            needs_tool = True
        if "cari " in t and "cari tahu" not in t and "cari tau" not in t:
            needs_tool = True
        if needs_tool:
            return ("fallback", "otak lokal menjawab teks padahal tugas ini butuh tool")
        return ("answer", raw.strip())

    def answer_with_context(self, task, tool_result):
        """Minta adapter merangkum hasil tool jadi jawaban singkat
        bahasa Indonesia. Kembalikan "" kalau gagal."""
        # Bentuk user SAMA seperti baris "merangkum hasil tool" di dataset
        # (mis. baris 52-53): instruction singkat + input "Hasil tool: ...".
        user = (
            "Rangkum hasil pengecekan ini untuk user dalam bahasa Indonesia.\n"
            f"Hasil tool: {str(tool_result)[:2000]}"
        )
        try:
            return self._generate(
                [
                    {"role": "system", "content": TRAINING_SYSTEM_PROMPT},
                    {"role": "user", "content": user},
                ]
            ).strip()
        except Exception:  # noqa: BLE001 - gagal merangkum = pakai ringkasan lokal
            return ""


def load_local_brain(adapter_dir=DEFAULT_ADAPTER_DIR, base=BASE_MODEL):
    """Muat otak lokal dan kembalikan LocalBrain yang sudah siap."""
    return LocalBrain(adapter_dir=adapter_dir, base=base).load()
