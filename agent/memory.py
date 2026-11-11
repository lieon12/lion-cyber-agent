"""Memori agen: pelajaran dari kesalahan + riwayat chat.

Pelajaran disimpan di agent/lessons.md (ikut di-commit, supaya
agen tidak mengulang kesalahan yang sama di mesin lain).
Riwayat chat disimpan lokal di .agent_memory.json (tidak di-commit).
"""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
LESSONS_FILE = BASE / "lessons.md"
HISTORY_FILE = BASE.parent / ".agent_memory.json"


def load_lessons():
    if not LESSONS_FILE.exists():
        return []
    text = LESSONS_FILE.read_text(encoding="utf-8")
    lessons = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("- "):
            lessons.append(line[2:].strip())
    return lessons


def add_lesson(mistake, fix, context=""):
    """Simpan satu pelajaran baru. Dipanggil saat agen salah / dikoreksi."""
    entry = f"- Kesalahan: {mistake} | Perbaikan: {fix}"
    if context:
        entry += f" | Konteks: {context}"
    text = LESSONS_FILE.read_text(encoding="utf-8") if LESSONS_FILE.exists() else "# Pelajaran\n\n"
    if mistake in text:
        return False
    if not text.endswith("\n"):
        text += "\n"
    LESSONS_FILE.write_text(text + entry + "\n", encoding="utf-8")
    return True


def load_history():
    if not HISTORY_FILE.exists():
        return []
    try:
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_history(history):
    HISTORY_FILE.write_text(
        json.dumps(history[-50:], indent=2, ensure_ascii=False), encoding="utf-8"
    )
