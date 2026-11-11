"""Skeleton fine-tune LoRA untuk model coder kecil.

Jalankan di Codespace dengan GPU atau Google Colab, bukan di mesin tanpa GPU.
Contoh:
    pip install torch transformers peft datasets accelerate
    python training/train_lora.py --base Qwen/Qwen2.5-Coder-1.5B --data dataset/dataset.jsonl
"""
import argparse

# Import berat hanya saat training, supaya `agent/` tetap ringan.
# from datasets import load_dataset
# from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
# from peft import LoraConfig, get_peft_model


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="Qwen/Qwen2.5-Coder-1.5B")
    ap.add_argument("--data", default="dataset/dataset.jsonl")
    ap.add_argument("--output", default="training/output")
    ap.add_argument("--epochs", type=int, default=2)
    args = ap.parse_args()
    print(f"Base: {args.base}")
    print(f"Data: {args.data} -> {args.output} ({args.epochs} epoch)")
    print("TODO: lengkapi dengan load_dataset + LoRA + Trainer di Codespace GPU.")
    print("Mulai dari 500-1000 contoh bagus, evaluasi di kode baru sebelum dipakai.")


if __name__ == "__main__":
    main()
