"""Tools internet untuk agen.

Ini adalah 'tangan' agen: modelnya sendiri tidak bisa internet,
tools inilah yang mengambil data live lalu diberikan ke model
untuk dianalisis.
"""
import importlib.util
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse


def fetch_url(url, timeout=15):
    """Ambil isi sebuah URL. Kembalikan judul, teks, dan header penting."""
    headers = {"User-Agent": "lion-cyber-agent/0.1 (audit website sendiri)"}
    r = requests.get(url, headers=headers, timeout=timeout)
    soup = BeautifulSoup(r.text, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    text = " ".join(soup.get_text(" ").split())[:8000]
    return {
        "url": url,
        "status": r.status_code,
        "final_url": r.url,
        "server": r.headers.get("Server", ""),
        "content_type": r.headers.get("Content-Type", ""),
        "title": soup.title.string.strip() if soup.title and soup.title.string else "",
        "text": text,
        "security_headers": {
            k: r.headers.get(k, "")
            for k in [
                "Strict-Transport-Security",
                "Content-Security-Policy",
                "X-Frame-Options",
                "X-Content-Type-Options",
            ]
        },
    }


def search_web(query, limit=5):
    """Cari di internet lewat DuckDuckGo HTML (tanpa API key)."""
    r = requests.get(
        "https://html.duckduckgo.com/html/",
        params={"q": query},
        headers={"User-Agent": "lion-cyber-agent/0.1"},
        timeout=15,
    )
    soup = BeautifulSoup(r.text, "html.parser")
    out = []
    for a in soup.select("a.result__a")[:limit]:
        out.append({"title": a.get_text(" ", strip=True), "url": a.get("href", "")})
    return out


def scan_sql(url, param="q"):
    """Jalankan tools/sql_scan.py ke website sendiri (payload aman, non-destruktif).

    Param default "q" adalah tebakan untuk form pencarian; kalau form
    target pakai nama lain, panggil dengan param itu, misal
    scan_sql(url, param="username"). Hasilnya: tidak ada sinyal kuat
    BUKAN berarti 100% aman — lanjutkan audit kode.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError(f"URL tidak valid untuk scan: {url}")
    spec = importlib.util.spec_from_file_location(
        "lion_sql_scan", Path(__file__).resolve().parent.parent / "tools" / "sql_scan.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.test_param(url, param)


def check_site_basic(url):
    """Cek dasar keamanan website sendiri: HTTPS, header, redirect."""
    parsed = urlparse(url)
    result = fetch_url(url)
    findings = []
    if parsed.scheme != "https":
        findings.append("Tidak memakai HTTPS — semua data bisa disadap.")
    else:
        findings.append("Memakai HTTPS.")
    h = result["security_headers"]
    if not h["Strict-Transport-Security"]:
        findings.append("Tidak ada header Strict-Transport-Security (HSTS).")
    if not h["Content-Security-Policy"]:
        findings.append("Tidak ada header Content-Security-Policy (CSP).")
    if not h["X-Frame-Options"]:
        findings.append("Tidak ada header X-Frame-Options — rentan clickjacking.")
    if not h["X-Content-Type-Options"]:
        findings.append("Tidak ada header X-Content-Type-Options.")
    result["findings"] = findings
    return result


# ---- Skill Kumar (v4): make.fun, GitHub, evaluasi diri ----
# NOTE 2026-11-14: scan_xss DIHAPUS dari file ini — tool XSS belum
# disetujui Lion (draft-nya masih di tools/xss_scan.py, lokal saja,
# belum di repo). Kalau ia setuju, kembalikan fungsi scan_xss di sini
# + daftarkan di agent/agent.py dan agent/validator.py.
# Modul-modul di tools/ dimuat dengan importlib seperti scan_sql,
# karena tools/ bukan package Python.

_TOOL_MODULES = {}


def _tool_module(name, filename):
    if name not in _TOOL_MODULES:
        spec = importlib.util.spec_from_file_location(
            f"lion_{name}", Path(__file__).resolve().parent.parent / "tools" / filename
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _TOOL_MODULES[name] = module
    return _TOOL_MODULES[name]


def list_open_competitions():
    """Daftar kompetisi make.fun yang sedang buka (read-only, butuh MAKEFUN_API_KEY)."""
    return _tool_module("makefun", "makefun.py").list_open_competitions()


def competition_status(slug):
    """Status satu kompetisi make.fun berdasarkan slug (read-only)."""
    return _tool_module("makefun", "makefun.py").competition_status(slug)


def my_entry_status(submission_id):
    """Status satu entry make.fun milik akun ini (read-only)."""
    return _tool_module("makefun", "makefun.py").my_entry_status(submission_id)


def entry_rank(slug, submission_id=None, handle=None):
    """Peringkat satu entry make.fun di leaderboard (read-only)."""
    return _tool_module("makefun", "makefun.py").entry_rank(
        slug, submission_id=submission_id, handle=handle
    )


def search_github_tools(query, limit=5):
    """Cari repo tool publik di GitHub (read-only, tanpa auth)."""
    return _tool_module("github_tools", "github_tools.py").search_github_tools(query, limit=limit)


def read_repo_file(owner, repo, path, ref=None):
    """Baca satu file dari repo publik GitHub (read-only)."""
    return _tool_module("github_tools", "github_tools.py").read_repo_file(owner, repo, path, ref=ref)


def vet_tool(repo_full_name):
    """Vetting repo GitHub sebelum dipakai sebagai tool (read-only, bukan izin pakai)."""
    return _tool_module("github_tools", "github_tools.py").vet_tool(repo_full_name)


def run_self_eval():
    """Evaluasi diri: uji tool sendiri ke target yang diizinkan, lalu nilai."""
    return _tool_module("self_eval", "self_eval.py").run_self_eval()
