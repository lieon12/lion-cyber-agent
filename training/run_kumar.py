#!/usr/bin/env python3
"""Jalankan Kumar hasil latihan percobaan (LoRA trial) dari laptop / VSCode.

Yang dibutuhkan:
  1. Python 3.10+ dan pip.
  2. pip install torch transformers peft accelerate
     (Di laptop tanpa GPU, torch CPU sudah cukup — model 0.5B jalan di CPU,
     hanya lebih lambat: beberapa detik per jawaban pendek. Kalau ada GPU
     NVIDIA, script ini otomatis memakainya.)
  3. Folder adapter hasil Colab: unzip kumar-lora-trial.zip di folder yang
     sama dengan script ini, sehingga ada ./kumar-lora-trial
     (berisi adapter_config.json, adapter_model.safetensors, dll).
     Adapter saja TIDAK cukup — model dasar (Qwen2.5-Coder-0.5B, ~1 GB)
     diunduh otomatis dari Hugging Face saat pertama kali jalan.

Cara pakai:
  python run_kumar.py              # jalankan 3 prompt uji (sama seperti di Colab)
  python run_kumar.py --chat       # mode chat interaktif, ketik 'keluar' untuk berhenti
  python run_kumar.py --adapter ./folder-lain

Catatan: ini adapter PERCOBAAN dari 37 contoh. Dua jawaban uji pertama
seharusnya keluar hampir sama dengan data latih (hafalan), yang ketiga
(soal baru) kemungkinan lemah. Itu normal — Kumar yang pintar baru datang
setelah dataset tumbuh ke 500+ contoh dan latih ulang.
"""

import argparse
import sys
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

BASE = "Qwen/Qwen2.5-Coder-0.5B"
SYSTEM = "Kamu adalah Kumar, asisten AI keamanan siber dan coding milik Lion. Jawablah dengan singkat dan benar."

TESTS = [
    # ADA di data latih (baris 1) — harusnya dihafal
    ("Tulis kode login PHP yang aman dari SQL injection.",
     "Bahasa: PHP, database MySQL, tabel users (username, password_hash)."),
    # ADA di data latih (baris 34) — harusnya dihafal
    ("Cek peringkat entry make.fun-ku di leaderboard kompetisi.",
     "Kompetisi food-picture-01, submission id 01a1d7b5-a669-73f8-8f3f-3b71817d2817."),
    # TIDAK ADA di data latih — ini tes sebenarnya (generalisasi)
    ("Tulis fungsi Python untuk memvalidasi email pengguna.",
     "Pakai regex, tolak email tanpa @ dan tanpa domain."),
]


def load(adapter_dir: Path):
    if not (adapter_dir / "adapter_config.json").exists():
        # Zip kadang ter-extract langsung (flat) tanpa subfolder: kalau
        # adapter_config.json ada di folder saat ini, pakai folder ini.
        if adapter_dir == Path("kumar-lora-trial") and (Path.cwd() / "adapter_config.json").exists():
            print("Adapter ditemukan langsung di folder ini (tanpa subfolder).")
            adapter_dir = Path.cwd()
        else:
            print(f"Adapter tidak ditemukan di {adapter_dir}")
            print("Unzip dulu kumar-lora-trial.zip di folder yang sama dengan script ini,")
            print("sehingga ada folder ./kumar-lora-trial berisi adapter_config.json,")
            print("atau jalankan dengan --adapter . kalau file adapter sudah langsung")
            print("di folder ini (tanpa subfolder).")
            sys.exit(1)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if device == "cuda" else torch.float32
    print(f"Perangkat: {device} ({torch.cuda.get_device_name(0) if device == 'cuda' else 'CPU, jawaban agak lambat'})")
    print(f"Memuat model dasar {BASE} ... (unduh ~1 GB kalau pertama kali)")

    tok = AutoTokenizer.from_pretrained(BASE)
    base = AutoModelForCausalLM.from_pretrained(
        BASE,
        torch_dtype=dtype,
        device_map="auto" if device == "cuda" else None,
        attn_implementation="sdpa",
    )
    if device == "cpu":
        base = base.to("cpu")
    model = PeftModel.from_pretrained(base, str(adapter_dir))
    model.eval()
    print("Adapter Kumar termuat.\n")
    return tok, model


def ask(tok, model, instruction: str, inp: str = "") -> str:
    user = instruction.strip() + (("\n" + inp.strip()) if inp.strip() else "")
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": user},
    ]
    text = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    ids = tok(text, return_tensors="pt").to(model.device)
    out = model.generate(**ids, max_new_tokens=256, do_sample=False,
                         pad_token_id=tok.eos_token_id)
    return tok.decode(out[0][ids["input_ids"].shape[1]:], skip_special_tokens=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Jalankan Kumar (LoRA trial).")
    parser.add_argument("--adapter", default="./kumar-lora-trial",
                        help="Folder adapter hasil unzip (default: ./kumar-lora-trial)")
    parser.add_argument("--chat", action="store_true",
                        help="Mode chat interaktif (bukan 3 prompt uji)")
    args = parser.parse_args()

    tok, model = load(Path(args.adapter))

    if args.chat:
        print("Mode chat — ketik pertanyaan, 'keluar' untuk berhenti.\n")
        while True:
            try:
                q = input("Kamu: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nSelesai.")
                break
            if q.lower() in ("keluar", "exit", "quit"):
                print("Selesai.")
                break
            if not q:
                continue
            print("Kumar:", ask(tok, model, q), "\n")
        return

    for i, (ins, inp) in enumerate(TESTS, 1):
        print(f"===== Uji {i}: {ins}")
        print(ask(tok, model, ins, inp))
        print()


if __name__ == "__main__":
    main()
