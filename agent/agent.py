"""Loop agen: pikir -> pilih tool -> jalankan -> simpulkan.

Model (otak) memutuskan tool apa yang dibutuhkan. Kalau tool
yang dibutuhkan belum ada, agen menulis tool baru (lihat
tools/sql_scan.py sebagai contoh pola itu), menyimpannya,
lalu menjalankannya.
"""
from .tools import fetch_url, search_web, check_site_basic

TOOLS = {
    "fetch_url": fetch_url,
    "search_web": search_web,
    "check_site_basic": check_site_basic,
}


def plan(task):
    """Perencana sederhana (v0): petakan kata kunci tugas ke tool.

    Di versi berikutnya, langkah ini diganti model yang sudah
    di-fine-tune dengan dataset/ agar bisa merencanakan sendiri.
    """
    t = task.lower()
    steps = []
    if "http" in t:
        url = [w for w in task.split() if w.startswith("http")][0]
        steps.append(("check_site_basic", {"url": url}))
        steps.append(("fetch_url", {"url": url}))
    if "cari" in t or "search" in t or "cve" in t or "owasp" in t:
        steps.append(("search_web", {"query": task}))
    if not steps:
        steps.append(("search_web", {"query": task}))
    return steps


def run(task):
    """Jalankan satu tugas dan kembalikan jejak langkah + hasil."""
    trace = []
    for name, kwargs in plan(task):
        fn = TOOLS[name]
        try:
            result = fn(**kwargs)
            trace.append({"tool": name, "kwargs": kwargs, "ok": True, "result": result})
        except Exception as e:  # noqa: BLE001 - laporkan error ke pengguna
            trace.append({"tool": name, "kwargs": kwargs, "ok": False, "error": str(e)})
    return trace
