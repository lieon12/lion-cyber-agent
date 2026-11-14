"""Loop agen: pikir -> pilih tool -> jalankan -> simpulkan.

Model (otak) memutuskan tool apa yang dibutuhkan. Kalau tool
yang dibutuhkan belum ada, agen menulis tool baru (lihat
tools/sql_scan.py sebagai contoh pola itu), menyimpannya,
lalu menjalankannya.
"""
import re

from .tools import (
    check_site_basic,
    competition_status,
    fetch_url,
    list_open_competitions,
    my_entry_status,
    read_repo_file,
    run_self_eval,
    scan_sql,
    search_github_tools,
    search_web,
    vet_tool,
)

TOOLS = {
    "fetch_url": fetch_url,
    "search_web": search_web,
    "check_site_basic": check_site_basic,
    "scan_sql": scan_sql,
    # Skill Kumar (v4) — lihat tools/makefun.py, tools/github_tools.py,
    # tools/self_eval.py. NOTE: scan_xss DIHAPUS 2026-11-14 — tool XSS
    # belum disetujui Lion (draft lokal di tools/xss_scan.py saja).
    "list_open_competitions": list_open_competitions,
    "competition_status": competition_status,
    "my_entry_status": my_entry_status,
    "search_github_tools": search_github_tools,
    "read_repo_file": read_repo_file,
    "vet_tool": vet_tool,
    "run_self_eval": run_self_eval,
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


def is_self_eval(task):
    """True kalau user minta agen menilai dirinya sendiri."""
    t = task.lower()
    return any(k in t for k in ("evaluasi diri", "nilai dirimu", "evaluasi dirimu", "nilai diri"))


def is_makefun(task):
    """True kalau user bertanya soal make.fun / bounty / kompetisi.

    UUID submission id juga cukup — itu hampir pasti maksudnya cek
    status entry make.fun.
    """
    t = task.lower()
    return any(k in t for k in ("make.fun", "makefun", "bounty", "kompetisi")) or bool(
        extract_submission_id(task)
    )


def is_github_tool(task):
    """True kalau user minta cari / baca / vetting tool di GitHub.

    Kata "github" tidak wajib — pola "owner/repo" + kata kerja
    (vetting, baca, cari tool) juga cukup.
    """
    t = task.lower()
    keywords = ("cari", "tool", "vet", "nilai", "periksa", "baca", "repo")
    if "github" in t and any(k in t for k in keywords):
        return True
    return bool(extract_repo(task)) and any(k in t for k in keywords)


def extract_submission_id(task):
    """Ambil submission id make.fun (UUID) dari teks, atau None."""
    m = re.search(
        r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
        task,
        re.IGNORECASE,
    )
    return m.group(0) if m else None


def extract_slug(task):
    """Ambil slug kompetisi dari URL /bounty/<slug> atau kata bersambung strip, atau None."""
    m = re.search(r"/bounty/([a-z0-9]+(?:-[a-z0-9]+)*)", task, re.IGNORECASE)
    if m:
        return m.group(1).lower()
    m = re.search(r"\b([a-z]{2,}(?:-[a-z0-9]+)+-[0-9]{2})\b", task, re.IGNORECASE)
    return m.group(1).lower() if m else None


def extract_repo(task):
    """Ambil 'owner/repo' dari teks, atau None.

    URL github.com/owner/repo juga dikenali — pola 'github.com/owner'
    yang salah tidak ikut terambil.
    """
    m = re.search(r"github\.com/([A-Za-z0-9_.\-]+)/([A-Za-z0-9_.\-]+)", task)
    if m:
        return f"{m.group(1)}/{m.group(2)}"
    text = re.sub(r"https?://\S+", "", task)
    m = re.search(r"\b([A-Za-z0-9_.\-]+)/([A-Za-z0-9_.\-]+)\b", text)
    if m:
        return f"{m.group(1)}/{m.group(2)}"
    return None


def extract_file_path(task):
    """Ambil path file (berakhiran .py/.md/.js/.txt/.json/.yaml/.yml) dari teks, atau None."""
    m = re.search(r"\b([A-Za-z0-9_.\-/]+\.(?:py|md|js|txt|json|ya?ml))\b", task)
    return m.group(1) if m else None


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

    # Evaluasi diri — jalankan self-eval, bukan cari tutorial.
    if is_self_eval(task):
        steps.append(("run_self_eval", {}))
        return steps

    # make.fun — bounty / kompetisi. Bukan pencarian web umum.
    if is_makefun(task):
        submission_id = extract_submission_id(task)
        if submission_id:
            steps.append(("my_entry_status", {"submission_id": submission_id}))
            return steps
        slug = extract_slug(task)
        if slug:
            steps.append(("competition_status", {"slug": slug}))
            return steps
        steps.append(("list_open_competitions", {}))
        return steps

    # GitHub — cari / baca / vetting tool. Jangan jalankan kode asing.
    if is_github_tool(task):
        repo = extract_repo(task)
        if repo and any(k in t for k in ("vet", "nilai", "periksa", "aman")):
            steps.append(("vet_tool", {"repo_full_name": repo}))
            return steps
        if repo and "baca" in t:
            path = extract_file_path(task)
            if path:
                steps.append(("read_repo_file", {"owner": repo.split("/")[0], "repo": repo.split("/")[1], "path": path}))
                return steps
        steps.append(("search_github_tools", {"query": task}))
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
