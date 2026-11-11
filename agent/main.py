"""CLI agen: python -m agent.main "cek https://website-kamu.example"

Hanya untuk website milikmu sendiri / yang kamu punya izin tertulis.
"""
import json
import sys

from .agent import run


def main():
    if len(sys.argv) < 2:
        print('Contoh: python -m agent.main "cek https://website-kamu.example"')
        raise SystemExit(2)
    task = " ".join(sys.argv[1:])
    print(f"Tugas: {task}\n")
    for step in run(task):
        print(f"== tool: {step['tool']} {step['kwargs']} ==")
        print(json.dumps(step.get("result") or step.get("error"), indent=2, ensure_ascii=False)[:4000])
        print()


if __name__ == "__main__":
    main()
