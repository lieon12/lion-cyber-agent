"""Validator: kode yang memutuskan apakah aksi agen boleh jalan.

Model hanya menyarankan. Validator yang menegakkan aturan Lion:
- hanya tool yang diizinkan
- hanya domain yang diizinkan (website sendiri)
- hanya payload non-destruktif
Kalau validator menolak, agen harus patuh — ini yang membuat agen
tetap menuruti Lion, bukan menuruti modelnya sendiri.
"""
import os
from urllib.parse import urlparse

ALLOWED_TOOLS = {"fetch_url", "search_web", "check_site_basic", "sql_scan"}

FORBIDDEN_PAYLOAD = ["drop ", "delete ", "update ", "insert ", "truncate ", "; drop", "or 1=1;"]


def allowed_domains():
    # verifydeal.site = website sendiri. example.com = situs uji aman.
    # testphp.vulnweb.com dan demo.owasp-juice.shop = situs uji publik yang
    # sengaja dibuat rentan untuk latihan keamanan, jadi boleh di-scan.
    raw = os.environ.get(
        "ALLOWED_DOMAINS",
        "verifydeal.site,example.com,testphp.vulnweb.com,demo.owasp-juice.shop",
    )
    return {d.strip().lower() for d in raw.split(",") if d.strip()}


def is_url_allowed(url):
    try:
        host = urlparse(url).netloc.lower()
    except Exception:
        return False
    # izinkan subdomain dari domain yang diizinkan
    return any(host == d or host.endswith("." + d) for d in allowed_domains())


def is_payload_safe(text):
    if not text:
        return True
    low = str(text).lower()
    return not any(bad in low for bad in FORBIDDEN_PAYLOAD)


def validate_tool_call(name, args):
    """Kembalikan (ok, alasan)."""
    if name not in ALLOWED_TOOLS:
        return False, f"Tool '{name}' tidak diizinkan. Tool yang diizinkan: {sorted(ALLOWED_TOOLS)}"
    args = args or {}
    url = args.get("url", "")
    if url and not is_url_allowed(url):
        return False, f"URL '{url}' tidak diizinkan. Hanya domain ini yang boleh di-scan: {sorted(allowed_domains())}"
    for key in ("param", "query", "payload"):
        if key in args and not is_payload_safe(args[key]):
            return False, f"Isi '{key}' mengandung kata yang dilarang (payload destruktif)."
    return True, "ok"
