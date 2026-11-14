"""Tool make.fun (read-only) untuk Kumar.

Hanya membaca (GET) dari API make.fun — daftar kompetisi yang buka,
status satu kompetisi, dan status entry sendiri. API key dibaca dari
variabel lingkungan MAKEFUN_API_KEY, tidak pernah ditulis di kode,
tidak pernah di-commit ke repo. Kalau key belum diatur, fungsi-fungsi
di sini mengembalikan error yang jelas, bukan mengarang data.

TIDAK ada fungsi submit atau claim di modul ini — mengirim entry
berarti uang/hadiah, jadi itu langkah yang diawasi: Lion harus
menyetujui setiap submit, dan submit dilakukan lewat kit CLI
(`node cli/makefun.mjs submit`) dengan transcript bundle, bukan
dari tool ini.

Endpoint yang dipakai (sudah terbukti dipakai 2026-11-14):
- GET /api/competitions?status=open (daftar kompetisi buka)
- GET /api/competitions/<slug> (detail satu kompetisi)
- GET /api/submissions/<id>/status (status satu entry)
- GET /api/competitions/<slug>/leaderboard (peringkat entry, dipakai entry_rank)
"""
import os

import requests

ORIGIN = "https://make.fun"
USER_AGENT = "lion-cyber-agent/0.1 (kumar, read-only)"


class MakefunError(Exception):
    """Error dari tool make.fun — key hilang, jaringan, atau API menolak."""


def _api_key():
    key = os.environ.get("MAKEFUN_API_KEY", "").strip()
    if not key:
        raise MakefunError(
            "MAKEFUN_API_KEY belum diatur. Isi di .env (MAKEFUN_API_KEY=...), "
            "jangan tulis key di chat atau commit ke repo. "
            "Key didapat dari proses connect akun make.fun."
        )
    return key


def _get(path, timeout=15):
    # Key dibaca DI LUAR try — key yang hilang bukan error jaringan,
    # dan pesannya harus bilang begitu, bukan "tidak bisa menghubungi".
    key = _api_key()
    try:
        r = requests.get(
            ORIGIN + path,
            headers={"x-api-key": key, "accept": "application/json", "User-Agent": USER_AGENT},
            timeout=timeout,
        )
    except Exception as e:  # noqa: BLE001
        raise MakefunError(f"Tidak bisa menghubungi {ORIGIN}{path}: {e}") from e
    if r.status_code != 200:
        raise MakefunError(f"API make.fun menolak {path}: HTTP {r.status_code}")
    try:
        data = r.json()
    except Exception as e:  # noqa: BLE001
        raise MakefunError(f"API make.fun mengembalikan bukan-JSON untuk {path}: {e}") from e
    return data.get("data", data) if isinstance(data, dict) else data


def _pick(d, *names, default=None):
    for n in names:
        if isinstance(d, dict) and d.get(n) is not None:
            return d[n]
    return default


def _count(v):
    if isinstance(v, list):
        return len(v)
    if isinstance(v, (int, float)):
        return v
    return None


def list_open_competitions():
    """Daftar kompetisi make.fun yang sedang buka.

    Kembalikan list dict: slug, title, prize_usd, status, ends_at, entries.
    """
    data = _get("/api/competitions?status=open")
    items = data if isinstance(data, list) else _pick(data, "competitions", "items", default=[]) or []
    out = []
    for c in items:
        if not isinstance(c, dict):
            continue
        out.append(
            {
                "slug": c.get("slug"),
                "title": _pick(c, "title", "name"),
                "prize_usd": _pick(c, "rewardAmount", "prize_usd", "prize_total_usd", "total_prize_usd", "potUsd"),
                "status": c.get("status"),
                "ends_at": _pick(c, "ends_at", "deadline", "end_time"),
                "entries": _count(_pick(c, "submissionCount", "entries_count", "entry_count", "submissions")),
            }
        )
    return out


def competition_status(slug):
    """Status satu kompetisi make.fun berdasarkan slug-nya.

    Halaman kompetisi di web ada di https://make.fun/bounty/<slug>
    (bukan /c/<slug> — itu 404, pelajaran 2026-11-14).
    """
    slug = (slug or "").strip().strip("/")
    if not slug:
        raise MakefunError("Slug kompetisi kosong. Contoh: food-picture-01")
    c = _get(f"/api/competitions/{slug}")
    if not isinstance(c, dict):
        raise MakefunError(f"Kompetisi '{slug}' tidak ditemukan di make.fun.")
    desc = (_pick(c, "description", "summary", default="") or "").replace("\n", " ")
    return {
        "slug": c.get("slug", slug),
        "title": _pick(c, "title", "name"),
        "prize_total_usd": _pick(c, "rewardAmount", "prize_total_usd", "prize_usd"),
        "entries_close": _pick(c, "deadline", "entries_close", "ends_at"),
        "submission_count": c.get("submissionCount"),
        "description": desc[:600],
        "page_url": f"https://make.fun/bounty/{slug}",
    }


def my_entry_status(submission_id):
    """Status satu entry milik akun ini berdasarkan submission id-nya.

    API memakai field "stage" untuk status entry (misal "submitted",
    "rejected") dan "problem" untuk alasan penolakan.
    """
    submission_id = (submission_id or "").strip()
    if not submission_id:
        raise MakefunError("Submission id kosong. Contoh: 01a1d76e-f7cb-7374-9ba8-626651d9752e")
    data = _get(f"/api/submissions/{submission_id}/status")
    if not isinstance(data, dict):
        raise MakefunError(f"Entry '{submission_id}' tidak ditemukan.")
    checks = data.get("checks", []) if isinstance(data.get("checks"), list) else []
    failed = [
        {"check": c.get("check"), "reason": c.get("reason"), "fix": c.get("fix")}
        for c in checks
        if isinstance(c, dict) and c.get("status") in ("fail", "failed", "rejected", "error")
    ]
    problem = data.get("problem") if isinstance(data.get("problem"), dict) else None
    return {
        "submission_id": submission_id,
        "status": _pick(data, "stage", "status", "state"),
        "outcome": data.get("outcome"),
        "competition": _pick(data, "competition", "competition_slug"),
        "checks": checks,
        "failed_checks": failed,
        "problem": {"title": problem.get("title"), "type": problem.get("type")} if problem else None,
        "deadlines": data.get("deadlines", {}),
        "raw": data,
    }


def _judge_record(entry):
    """Ambil rekor juri (menang/seri/kalah) dari satu baris leaderboard."""
    judge = entry.get("judge")
    if not isinstance(judge, dict):
        judge = (entry.get("performance") or {}).get("judge") or {}
    if not isinstance(judge, dict):
        return {}
    return judge


def entry_rank(slug, submission_id=None, handle=None):
    """Peringkat satu entry di leaderboard kompetisi make.fun.

    GET /api/competitions/<slug>/leaderboard. Cari entry akun ini
    berdasarkan submission id atau handle. Kembalikan rank, prize_rank,
    rekor juri (menang/seri/kalah/pertandingan), total entry yang
    terdaftar, dan baris peringkat 100 (batas zona hadiah).

    Kalau slug tidak disebut tapi submission id ada, slug dicari dulu
    lewat my_entry_status. Kalau entry tidak ada di leaderboard,
    katakan begitu — peringkat tidak pernah dikarang.
    """
    slug = (slug or "").strip().strip("/")
    submission_id = (submission_id or "").strip() or None
    handle = (handle or "").strip().lstrip("@") or None
    if not slug and submission_id:
        slug = (my_entry_status(submission_id).get("competition") or "").strip()
    if not slug:
        raise MakefunError("Slug kompetisi kosong. Contoh: food-picture-01")
    if not submission_id and not handle:
        raise MakefunError(
            "Untuk cek peringkat, berikan submission id entry-nya atau handle akun "
            "(contoh: entry_rank('food-picture-01', submission_id='01a1d7b5-...') "
            "atau entry_rank('food-picture-01', handle='qjack'))."
        )
    data = _get(f"/api/competitions/{slug}/leaderboard")
    if not isinstance(data, dict):
        raise MakefunError(f"Leaderboard '{slug}' tidak ditemukan di make.fun.")
    entries = data.get("entries", [])
    if not isinstance(entries, list):
        entries = []
    mine = None
    for e in entries:
        if not isinstance(e, dict):
            continue
        if submission_id and e.get("submission_id") == submission_id:
            mine = e
            break
        if handle and (e.get("handle") or "").lower() == handle.lower():
            mine = e
            break
    if mine is None:
        raise MakefunError(
            f"Entry tidak ada di leaderboard '{slug}' — mungkin belum dinilai, "
            f"atau submission id/handle salah. Peringkat tidak bisa dikarang."
        )
    judge = _judge_record(mine)
    cutoff = None
    for e in entries:
        if isinstance(e, dict) and e.get("rank") == 100:
            cj = _judge_record(e)
            cutoff = {
                "rank": 100,
                "handle": e.get("handle"),
                "wins": cj.get("wins"),
                "draws": cj.get("draws"),
                "losses": cj.get("losses"),
                "matches": cj.get("matches"),
            }
            break
    rank = mine.get("rank")
    return {
        "slug": slug,
        "submission_id": mine.get("submission_id"),
        "handle": mine.get("handle"),
        "title": mine.get("title"),
        "rank": rank,
        "prize_rank": mine.get("prize_rank"),
        "wins": judge.get("wins"),
        "draws": judge.get("draws"),
        "losses": judge.get("losses"),
        "matches": judge.get("matches"),
        "total_entries": len(entries),
        "in_prize_zone": isinstance(rank, int) and rank <= 100,
        "rank_100_cutoff": cutoff,
        "page_url": f"https://make.fun/bounty/{slug}",
    }
