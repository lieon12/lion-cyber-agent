"""Tool GitHub untuk Kumar: cari, baca, dan VETTING tool dari repo publik.

GitHub adalah perpustakaan tool — Kumar bisa mencari tool (misalnya
scanner XSS), membaca README dan kodenya, lalu menilai apakah tool itu
aman dan cocok sebelum dipakai.

Vetting SAJA: tidak pernah clone, tidak pernah download-dan-jalankan,
tidak pernah mengeksekusi kode asing. Mengadopsi tool yang lolos
vetting adalah langkah terpisah yang butuh persetujuan Lion — tool
yang belum divetting tidak boleh dijalankan, apa pun kata modelnya.

API GitHub publik tidak butuh auth (60 request/jam). Kalau
GITHUB_TOKEN diisi di .env, batasnya naik (5000 request/jam).
Token tidak pernah ditulis di kode atau di-commit.
"""
import os
import re

import requests

API = "https://api.github.com"
USER_AGENT = "lion-cyber-agent/0.1 (kumar, vetting-only)"
MAX_FILE_CHARS = 8000

# Pola kode yang berbahaya. Sekadar pola — vetting selalu butuh
# tinjauan manusia sebelum adopsi, pola di sini hanya menangkap
# yang jelas-jelas mencurigakan.
DANGEROUS_PATTERNS = [
    (r"os\.system\s*\(", "menjalankan perintah shell via os.system"),
    (r"subprocess\.(call|run|Popen|check_output)\s*\(", "menjalankan proses shell via subprocess"),
    (r"(?<![\w.])eval\s*\(", "eval() — mengeksekusi string sebagai kode"),
    (r"(?<![\w.])exec\s*\(", "exec() — mengeksekusi string sebagai kode"),
    (r"__import__\s*\(", "__import__ dinamis — kode tersembunyi"),
    (r"getpass|keyring|readline.*password", "mengakses kredensial / password"),
    (r"open\s*\(\s*['\"]/(etc|proc|root)", "membaca file sistem"),
    (r"requests\.(post|put|patch)\s*\(", "mengirim data ke jaringan (periksa datanya!)"),
    (r"socket\.socket|urllib\.request\.urlopen", "koneksi jaringan mentah"),
    (r"base64\.b64decode\s*\([^)]*\)\s*(;|\n|\r)", "decode base64 yang langsung dipakai"),
]


class GithubError(Exception):
    """Error dari tool GitHub — repo tidak ada, rate limit, atau jaringan.

    kind: "not_found" | "rate_limit" | "network" | "api".
    Vetting harus membedakan: 404 berarti "tidak ada", tapi rate limit
    berarti "tidak tahu" — jangan pernah mencatat fakta dari kegagalan
    yang bukan 404.
    """

    def __init__(self, message, kind="api"):
        super().__init__(message)
        self.kind = kind


def _headers():
    h = {"Accept": "application/vnd.github+json", "User-Agent": USER_AGENT}
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def _get(path, timeout=15):
    try:
        r = requests.get(API + path, headers=_headers(), timeout=timeout)
    except Exception as e:  # noqa: BLE001
        raise GithubError(f"Tidak bisa menghubungi api.github.com{path}: {e}", kind="network") from e
    if r.status_code == 404:
        raise GithubError(f"Tidak ditemukan di GitHub: {path}", kind="not_found")
    if r.status_code == 403 and "rate limit" in r.text.lower():
        raise GithubError(
            "Rate limit API GitHub habis (60/jam tanpa token). Isi GITHUB_TOKEN di .env atau tunggu.",
            kind="rate_limit",
        )
    if r.status_code != 200:
        raise GithubError(f"API GitHub menolak {path}: HTTP {r.status_code}", kind="api")
    return r.json()


def search_github_tools(query, limit=5):
    """Cari repo publik di GitHub yang cocok dengan query (misal 'xss scanner').

    Kembalikan list dict: full_name, description, stars, language,
    license, url. Diurutkan berdasarkan bintang.
    """
    query = (query or "").strip()
    if not query:
        raise GithubError("Query pencarian kosong. Contoh: xss scanner python")
    data = _get(f"/search/repositories?q={requests.utils.quote(query)}&sort=stars&order=desc&per_page={int(limit)}")
    out = []
    for item in data.get("items", []):
        lic = item.get("license") or {}
        out.append(
            {
                "full_name": item.get("full_name"),
                "description": item.get("description"),
                "stars": item.get("stargazers_count"),
                "language": item.get("language"),
                "license": lic.get("spdx_id") or lic.get("name"),
                "url": item.get("html_url"),
            }
        )
    return out


def read_repo_file(owner, repo, path, ref=None):
    """Baca satu file dari repo publik lewat GitHub contents API.

    Kembalikan dict: owner, repo, path, size, sha, content (dibatasi
    8000 karakter pertama). Tidak men-download repo, tidak menjalankan
    apa pun — hanya membaca.
    """
    owner = (owner or "").strip()
    repo = (repo or "").strip()
    path = (path or "").strip().lstrip("/")
    if not owner or not repo or not path:
        raise GithubError("Butuh owner, repo, dan path. Contoh: read_repo_file('OWASP', 'juice-shop', 'README.md')")
    q = f"?ref={requests.utils.quote(ref)}" if ref else ""
    data = _get(f"/repos/{owner}/{repo}/contents/{path}{q}")
    if isinstance(data, list):
        raise GithubError(f"'{path}' adalah folder, bukan file. Sebutkan path file-nya.")
    import base64

    content = data.get("content", "")
    try:
        text = base64.b64decode(content).decode("utf-8", errors="replace")
    except Exception:
        text = ""
    return {
        "owner": owner,
        "repo": repo,
        "path": path,
        "size": data.get("size"),
        "sha": data.get("sha"),
        "content": text[:MAX_FILE_CHARS],
        "truncated": len(text) > MAX_FILE_CHARS,
    }


def _scan_text(text, filename):
    hits = []
    for lineno, line in enumerate(text.splitlines(), 1):
        for pattern, desc in DANGEROUS_PATTERNS:
            if re.search(pattern, line):
                hits.append({"file": filename, "line": lineno, "pattern": desc, "code": line.strip()[:200]})
    return hits


def vet_tool(repo_full_name):
    """Vetting repo publik sebelum dipakai sebagai tool.

    Yang diperiksa (read-only): ada README? lisensi? berapa bintang?
    apakah repo diarsipkan? dan apakah kode di file utama mengandung
    pola berbahaya (shell, eval, kirim kredensial, obfuscation).

    Kembalikan dict dengan checklist + verdict:
    - "layak ditinjau lanjut" — tidak ada temuan pola berbahaya
    - "butuh tinjauan manual" — ada temuan yang harus dibaca manusia
    - "jangan pakai" — repo diarsipkan / tanpa lisensi / pola jelas berbahaya

    Verdict BUKAN izin pakai — adopsi tool tetap butuh persetujuan Lion.
    """
    name = (repo_full_name or "").strip()
    if "/" not in name:
        raise GithubError("Nama repo harus 'owner/repo'. Contoh: OWASP/juice-shop")
    owner, repo = [p.strip() for p in name.split("/", 1)]
    if not owner or not repo:
        raise GithubError("Nama repo harus 'owner/repo'. Contoh: OWASP/juice-shop")

    info = _get(f"/repos/{owner}/{repo}")
    lic = info.get("license") or {}
    checklist = {
        "repo": info.get("full_name"),
        "description": info.get("description"),
        "stars": info.get("stargazers_count"),
        "language": info.get("language"),
        "license": lic.get("spdx_id") or lic.get("name"),
        "archived": bool(info.get("archived")),
        "default_branch": info.get("default_branch"),
        "url": info.get("html_url"),
    }

    # README: ada dan sepanjang apa. Hanya 404 yang berarti "tidak ada" —
    # rate limit / jaringan harus gagal dengan keras, bukan dicatat
    # sebagai "tidak ada README" (itu kesimpulan yang salah).
    try:
        readme = _get(f"/repos/{owner}/{repo}/readme")
        import base64

        readme_text = base64.b64decode(readme.get("content", "")).decode("utf-8", errors="replace")
        checklist["has_readme"] = True
        checklist["readme_chars"] = len(readme_text)
    except GithubError as e:
        if e.kind != "not_found":
            raise
        checklist["has_readme"] = False
        checklist["readme_chars"] = 0

    # Pindai file kode di root repo (maks 3 file, masing-masing dibatasi).
    # Sama seperti README: hanya 404 yang boleh dilewati diam-diam.
    findings = []
    try:
        listing = _get(f"/repos/{owner}/{repo}/contents/")
    except GithubError as e:
        if e.kind != "not_found":
            raise
        listing = []
    code_files = [
        e["name"]
        for e in listing
        if isinstance(e, dict) and e.get("type") == "file" and e["name"].endswith((".py", ".js", ".sh", ".rb", ".go"))
    ][:3]
    for fname in code_files:
        try:
            f = read_repo_file(owner, repo, fname)
            findings.extend(_scan_text(f["content"], fname))
        except GithubError as e:
            if e.kind != "not_found":
                raise
            continue
    checklist["dangerous_patterns"] = findings

    # Verdict — konservatif: kalau ragu, minta tinjauan manual.
    if checklist["archived"]:
        verdict = "jangan pakai"
        reason = "Repo diarsipkan (tidak dirawat lagi)."
    elif not checklist["license"]:
        verdict = "butuh tinjauan manual"
        reason = "Tidak ada lisensi — tidak jelas boleh dipakai atau tidak."
    elif findings:
        verdict = "butuh tinjauan manual"
        reason = f"Ditemukan {len(findings)} pola mencurigakan di kode — harus dibaca manusia dulu."
    elif not checklist["has_readme"]:
        verdict = "butuh tinjauan manual"
        reason = "Tidak ada README — tidak jelas tool ini apa dan cara pakainya."
    else:
        verdict = "layak ditinjau lanjut"
        reason = "Tidak ada pola berbahaya yang terdeteksi di file utama; tetap butuh persetujuan Lion sebelum dipakai."
    checklist["verdict"] = verdict
    checklist["verdict_reason"] = reason
    checklist["note"] = "Vetting bukan izin pakai. Adopsi tool tetap butuh persetujuan Lion."
    return checklist
