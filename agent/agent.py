"""Loop agen: pikir -> pilih tool -> jalankan -> simpulkan.

Model (otak) memutuskan tool apa yang dibutuhkan. Kalau tool
yang dibutuhkan belum ada, agen menulis tool baru (lihat
tools/sql_scan.py sebagai contoh pola itu), menyimpannya,
lalu menjalankannya.
"""
import re

from .tools import fetch_url, scan_sql, search_web, check_site_basic

TOOLS = {
    "fetch_url": fetch_url,
    "search_web": search_web,
    "check_site_basic": check_site_basic,
    "scan_sql": scan_sql,
}


def extract_url(task):
    """Ambil URL pertama dari teks, atau None."""
    m = re.search(r"https?://[^\s\"'<>]+", task)
    return m.group(0).rstrip(".,)") if m else None


def extract_param(task, default="q"):
    """Ambil nama parameter dari 'param <nama>' / 'param=<nama>', atau default."""
    m = re.search(r"param(?:eter)?\s*[=:]\s*([A-Za-z0-9_\-\[\]]+)", task, re.IGNORECASE)
    if m:
        return m.group(1)
    m = re.search(r"\bparam\s+([A-Za-z0-9_\-\[\]]+)", task, re.IGNORECASE)
    return m.group(1) if m else default


def is_sql_scan(task):
    """True kalau user minta scan SQL — ini BUKAN permintaan cari tutorial.

    Pelajaran 6 (2026-11-11): 'lanjut scan SQL-nya' pernah dijawab
    dengan search_web. Jangan ulangi: jalankan scan_sql ke URL terakhir.
    """
    t = task.lower()
    return "sql" in t and any(k in t for k in ("scan", "injection", "sqli", "injeksi"))


def plan(task, last_url=None):
    """Perencana sederhana (v0): petakan kata kunci tugas ke tool.

    Di versi berikutnya, langkah ini diganti model yang sudah
    di-fine-tune dengan dataset/ agar bisa merencanakan sendiri.
    """
    t = task.lower()
    steps = []
    url = extract_url(task) or last_url

    # Scan SQL dulu — dan jangan jatuh ke search_web untuk perintah ini.
    if is_sql_scan(task):
        if url:
            steps.append(("scan_sql", {"url": url, "param": extract_param(task)}))
        # Tanpa URL, kembalikan langkah kosong: chat.py akan menanyakan
        # URL-nya ke user, bukan malah mencari tutorial di web.
        return steps

    if "http" in t:
        url = extract_url(task)
        steps.append(("check_site_basic", {"url": url}))
        steps.append(("fetch_url", {"url": url}))
    # Jangan cari di web hanya karena URL-nya mengandung kata "owasp" —
    # itu yang membuat "cek https://demo.owasp-juice.shop/" kemarin
    # malah menjalankan search_web yang tidak perlu.
    elif "cari" in t or "search" in t or "cve" in t or "owasp" in t:
        steps.append(("search_web", {"query": task}))
    if not steps:
        steps.append(("search_web", {"query": task}))
    return steps


def run(task, last_url=None):
    """Jalankan satu tugas dan kembalikan jejak langkah + hasil."""
    trace = []
    for name, kwargs in plan(task, last_url=last_url):
        fn = TOOLS[name]
        try:
            result = fn(**kwargs)
            trace.append({"tool": name, "kwargs": kwargs, "ok": True, "result": result})
        except Exception as e:  # noqa: BLE001 - laporkan error ke pengguna
            trace.append({"tool": name, "kwargs": kwargs, "ok": False, "error": str(e)})
    return trace
