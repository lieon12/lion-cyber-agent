#!/usr/bin/env python3
"""Latih LoRA Kumar — script latihan yang bisa dipakai ulang.

Ini script yang sama dengan notebook percobaan yang sudah terbukti jalan
(`training/kumar-trial-train.ipynb`, diuji Lion di Colab 2026-11-14),
ditulis ulang sebagai script supaya latihan berikutnya tidak perlu
notebook dan tidak mengulang 3 error yang sama:

1. torchao: peft butuh torchao >= 0.16.0, Colab memasang 0.10.0.
   torchao tidak dibutuhkan untuk LoRA biasa — solusinya
   `pip uninstall -y torchao` lalu restart session (langkah env,
   dilakukan SEBELUM menjalankan script ini, bukan di dalam script).
2. warmup_ratio: transformers terbaru sudah tidak mengenal argumen ini,
   diganti `warmup_steps=2` (lihat TrainingArguments di bawah).
3. Padding labels: collator transformers terbaru tidak lagi mem-pad
   `labels`, jadi kalau panjang contoh beda-beda (mis. 132 vs 191 token)
   batch gagal dibentuk. Solusinya: semua contoh di-pad ke MAX_LEN=512
   di dalam `tokenize()` (lihat fungsi itu).

Yang dibutuhkan:
  - GPU (Colab T4 gratis sudah cukup untuk dataset saat ini (131 contoh, 2026-11-14); tanpa GPU script
    berhenti dengan pesan yang jelas — jangan latih di CPU).
  - pip install torch transformers peft datasets accelerate
  - File dataset: dataset/dataset.jsonl (format tiap baris:
    {"instruction": ..., "input": ..., "output": ...})

Cara pakai (di Colab, setelah upload dataset.jsonl ke folder kerja):
    !pip uninstall -y torchao        # sekali per sesi, lalu restart session
    !python training/train_lora.py --data dataset.jsonl --output kumar-lora-v2

  atau di mesin GPU sendiri:
    python training/train_lora.py --data dataset/dataset.jsonl --output training/output

Setelah selesai, adapter tersimpan di --output. Uji dari laptop/VSCode:
    python training/run_kumar.py --adapter <output>

Catatan jujur: dengan 131 contoh, hasil latihan masih banyak menghafal contohnya,
bukan memahami ilmunya. Script ini membuktikan jalur latihannya jalan.
Kumar yang benar-benar pintar baru datang setelah dataset tumbuh ke
500+ contoh, lalu latih ulang dengan data itu (cukup ganti --data).
"""

import argparse
import json
import sys
from pathlib import Path

SYSTEM = "Kamu adalah Kumar, asisten AI keamanan siber dan coding milik Lion. Jawablah dengan singkat dan benar."
MAX_LEN = 512

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


def format_row(r):
    user = r["instruction"].strip()
    if r["input"].strip():
        user += "\n" + r["input"].strip()
    return (
        "<|im_start|>system\n" + SYSTEM + "<|im_end|>\n"
        "<|im_start|>user\n" + user + "<|im_end|>\n"
        "<|im_start|>assistant\n" + r["output"].strip() + "<|im_end|>"
    )


def load_rows(data_path):
    rows = [json.loads(line) for line in open(data_path, encoding="utf-8") if line.strip()]
    assert rows, f"Dataset kosong: {data_path}"
    assert all(set(r.keys()) == {"instruction", "input", "output"} for r in rows), (
        "Format baris bukan instruction/input/output!"
    )
    return rows


def main():
    ap = argparse.ArgumentParser(description="Latih LoRA Kumar (Qwen2.5-Coder-0.5B).")
    ap.add_argument("--base", default="Qwen/Qwen2.5-Coder-0.5B",
                    help="Model dasar (default: Qwen/Qwen2.5-Coder-0.5B, sama seperti notebook trial).")
    ap.add_argument("--data", default="dataset/dataset.jsonl", help="File dataset.jsonl.")
    ap.add_argument("--output", default="kumar-lora-trial", help="Folder output adapter.")
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--max-len", type=int, default=MAX_LEN)
    ap.add_argument("--eval", action="store_true",
                    help="Setelah latih, jawab 3 prompt uji (2 dari data latih, 1 baru).")
    args = ap.parse_args()

    # Import berat hanya di sini, supaya --help tetap jalan tanpa torch.
    try:
        import torch
    except ImportError:
        print("ERROR: torch belum terpasang. Jalankan: pip install torch transformers peft datasets accelerate",
              file=sys.stderr)
        sys.exit(1)
    if not torch.cuda.is_available():
        print("ERROR: TIDAK ADA GPU. Latihan ini WAJIB GPU — di Colab pilih "
              "Runtime -> Change runtime type -> T4 GPU, lalu jalankan ulang.",
              file=sys.stderr)
        sys.exit(1)
    print(f"GPU: {torch.cuda.get_device_name(0)}")

    try:
        from datasets import Dataset
        from transformers import (AutoModelForCausalLM, AutoTokenizer,
                                  Trainer, TrainingArguments,
                                  DataCollatorForLanguageModeling)
        from peft import LoraConfig, get_peft_model
    except ImportError as e:
        # Penyebab paling umum: torchao versi lama di Colab (0.10.0) membuat
        # peft gagal diimpor. torchao tidak dibutuhkan untuk LoRA biasa.
        print(f"ERROR: gagal impor pustaka latihan: {e}", file=sys.stderr)
        print("Kalau menyebut torchao: jalankan `pip uninstall -y torchao`, "
              "lalu Runtime -> Restart session, baru jalankan script ini lagi.",
              file=sys.stderr)
        sys.exit(1)

    rows = load_rows(args.data)
    print(f"Jumlah contoh: {len(rows)} dari {args.data}")
    texts = [format_row(r) for r in rows]

    tokenizer = AutoTokenizer.from_pretrained(args.base)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        args.base, torch_dtype=torch.float16, device_map="auto",
        attn_implementation="sdpa",
    )
    model.config.use_cache = False

    def tokenize(text):
        # Loss hanya dihitung pada jawaban (assistant), prompt di-mask dengan -100.
        # Semua contoh di-pad ke MAX_LEN di sini, supaya batch selalu sama panjang:
        # collator di transformers terbaru tidak lagi mem-pad labels, jadi kalau
        # panjang contoh beda-beda (mis. 132 vs 191 token) batch-nya gagal dibentuk.
        prompt = text.split("<|im_start|>assistant\n")[0] + "<|im_start|>assistant\n"
        full_ids = tokenizer(text, truncation=True, max_length=args.max_len)["input_ids"]
        prompt_ids = tokenizer(prompt, truncation=True, max_length=args.max_len)["input_ids"]
        n = min(len(prompt_ids), len(full_ids))
        labels = ([-100] * n + full_ids[n:])[:args.max_len]
        pad_len = args.max_len - len(full_ids)
        input_ids = full_ids + [tokenizer.pad_token_id] * pad_len
        labels = labels + [-100] * pad_len
        attention_mask = [1] * len(full_ids) + [0] * pad_len
        return {"input_ids": input_ids, "labels": labels, "attention_mask": attention_mask}

    ds = Dataset.from_list([{"text": t} for t in texts])
    ds = ds.map(lambda ex: tokenize(ex["text"]), remove_columns=["text"])

    peft_cfg = LoraConfig(
        r=8, lora_alpha=16, lora_dropout=0.05,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                        "gate_proj", "up_proj", "down_proj"],
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, peft_cfg)
    model.print_trainable_parameters()

    # PERBAIKAN (2026-11-14): warmup_ratio sudah tidak dikenal transformers
    # terbaru — pakai warmup_steps=2.
    training_args = TrainingArguments(
        output_dir=args.output,
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        num_train_epochs=args.epochs,
        learning_rate=2e-4,
        lr_scheduler_type="cosine",
        warmup_steps=2,
        logging_steps=5,
        save_strategy="no",
        fp16=True,
        report_to="none",
        optim="adamw_torch",
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=ds,
        data_collator=DataCollatorForLanguageModeling(tokenizer, mlm=False),
    )
    trainer.train()

    model.save_pretrained(args.output)
    tokenizer.save_pretrained(args.output)
    print(f"\nSelesai. Adapter tersimpan di {args.output}")
    print(f"Uji dari laptop/VSCode: python training/run_kumar.py --adapter {args.output}")

    if args.eval:
        from peft import PeftModel

        base = AutoModelForCausalLM.from_pretrained(
            args.base, torch_dtype=torch.float16, device_map="auto",
            attn_implementation="sdpa",
        )
        eval_model = PeftModel.from_pretrained(base, args.output)
        eval_model.eval()

        def ask(instruction, inp=""):
            user = instruction.strip() + (("\n" + inp.strip()) if inp.strip() else "")
            messages = [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": user},
            ]
            text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            ids = tokenizer(text, return_tensors="pt").to(eval_model.device)
            out = eval_model.generate(**ids, max_new_tokens=256, do_sample=False,
                                      pad_token_id=tokenizer.eos_token_id)
            return tokenizer.decode(out[0][ids["input_ids"].shape[1]:], skip_special_tokens=True)

        for i, (ins, inp) in enumerate(TESTS, 1):
            print(f"\n===== Uji {i}: {ins}")
            print(ask(ins, inp))


if __name__ == "__main__":
    main()
