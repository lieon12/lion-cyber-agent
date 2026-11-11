"""Otak Gemini (v3) — via Gemini API (REST, hanya pakai requests).

Tidak ada API key? Fungsi has_api_key() mengembalikan False dan
chat.py fallback ke mode rule-based v2.

API key TIDAK boleh ditulis di chat atau di-commit ke repo.
Isi di file .env di Codespace:
    GEMINI_API_KEY=...
    GEMINI_MODEL=gemini-3.8-flash
"""
import json
import os
from pathlib import Path

import requests

try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except Exception:
    pass


def _load_system_prompt():
    p = Path(__file__).resolve().parent / "system_prompt.md"
    return p.read_text(encoding="utf-8") if p.exists() else "Kamu agen keamanan siber."


def has_api_key():
    return bool(os.environ.get("GEMINI_API_KEY", "").strip())


def model_name():
    return os.environ.get("GEMINI_MODEL", "gemini-3.8-flash").strip()


def ask_gemini(user_text, lessons, history, last_url=None):
    """Tanya Gemini. Kembalikan dict: reply / tool_call / error."""
    if not has_api_key():
        return {"error": "no_api_key"}
    model = model_name()
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}"
        f":generateContent?key={os.environ['GEMINI_API_KEY']}"
    )
    context = []
    if lessons:
        context.append("Pelajaran dari kesalahan sebelumnya:\n" + "\n".join(f"- {l}" for l in lessons))
    if last_url:
        context.append(f"URL terakhir yang dicek: {last_url}")
    if history:
        recent = history[-6:]
        context.append("Riwayat singkat:\n" + "\n".join(f"{h.get('role')}: {h.get('content')}" for h in recent))
    prompt = "\n\n".join(context + [f"Perintah user: {user_text}"])
    payload = {
        "system_instruction": {"parts": [{"text": _load_system_prompt()}]},
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2},
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
        ],
    }
    try:
        r = requests.post(url, json=payload, timeout=60)
    except Exception as e:  # noqa: BLE001
        return {"error": f"request_failed: {e}"}
    if r.status_code != 200:
        return {"error": f"gemini_http_{r.status_code}: {r.text[:500]}"}
    try:
        data = r.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:  # noqa: BLE001
        return {"error": f"parse_failed: {e} | raw: {r.text[:500]}"}
    # Jika model menjawab dengan JSON tool-call, parse itu.
    tool_call = None
    if text.startswith("{") and '"tool"' in text:
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict) and "tool" in parsed:
                tool_call = parsed
                text = ""
        except Exception:
            pass
    return {"reply": text, "tool_call": tool_call}
