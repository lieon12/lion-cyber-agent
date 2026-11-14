"""Pengukur kemampuan agen — persen yang bisa diaudit, bukan karangan.

Cara hitung (target yang dipakai ada di bawah, bisa diubah kalau Lion mau):
- Coding % = 50% * (contoh dataset / 500) + 30% * (topik coding yang ada / 20)
              + 20% * (tool yang sudah dibuat / 10)
- Hacking % = 50% * (kategori OWASP yang sudah ada tool/ujinya / 10)
              + 30% * (situs yang berhasil diuji / 5)
              + 20% * (temuan terkonfirmasi / 20)

Topik coding dihitung dari kata kunci di dataset.jsonl.
Kategori OWASP yang sudah ada tool/ujinya saat ini: secure headers
(check_site_basic) dan SQL injection (scan_sql) = 2 dari 10.
Situs yang berhasil diuji dihitung dari laporan terakhir di reports/.
Temuan terkonfirmasi dihitung dari laporan terakhir (header hilang, dll).

Persen ini adalah perkiraan dari cakupan, bukan nilai ujian resmi.
Naiknya persen berarti dataset, tool, dan temuan bertambah — bukan
berarti agen tiba-tiba jadi ahli.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CODING_TOPICS = [
    "sql", "xss", "csrf", "access", "auth", "password", "upload",
    "header", "session", "redirect", "rate", "hash", "validasi",
    "injection", "sensitive", "audit", "login", "file", "cookie", "token",
]

OWASP_COVERED = ["secure headers", "sql injection"]  # ada tool/uji yang jalan
# NOTE: "cross-site scripting (xss)" DIHAPUS sementara 2026-11-13 — tool scan_xss
# belum disetujui Lion (hanya ada di mesin lab, belum di repo), jadi tidak
# boleh dihitung sampai ia menyetujui. Kalau ia setuju, tambahkan kembali
# "cross-site scripting (xss)" di sini + "scan_xss" di _count_tools().


def _count_dataset():
    p = ROOT / "dataset" / "dataset.jsonl"
    if not p.exists():
        return 0, set()
    rows = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
    text = " ".join((r.get("instruction", "") + " " + r.get("input", "")).lower() for r in rows)
    topics = {t for t in CODING_TOPICS if t in text}
    return len(rows), topics


def _count_lessons():
    p = ROOT / "agent" / "lessons.md"
    if not p.exists():
        return 0
    return p.read_text(encoding="utf-8").count("- Kesalahan:")


def _count_tools():
    # Tool internet yang terdaftar di agent/tools.py + tools/sql_scan.py.
    # "scan_xss" DIHAPUS sementara 2026-11-13 (lihat OWASP_COVERED di atas):
    # tools/xss_scan.py belum disetujui Lion dan belum ada di repo.
    tools = ["fetch_url", "search_web", "check_site_basic", "scan_sql"]
    return tools


def _last_report_stats():
    # Hanya laporan harian (YYYY-MM-DD.json) — file lain di reports/
    # seperti self-eval-latest.json tidak punya per_target dan akan
    # membuat situs/temuan terhitung 0 (bug 2026-11-15: Hacking 10%).
    reports = sorted(
        p for p in (ROOT / "reports").glob("*.json")
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}\.json", p.name)
    )
    if not reports:
        return 0, 0
    data = json.loads(reports[-1].read_text(encoding="utf-8"))
    per_target = data.get("per_target", {})
    sites_ok = 0
    findings = 0
    for target, lines in per_target.items():
        joined = "\n".join(lines)
        if "status 200" in joined:
            sites_ok += 1
        findings += joined.count("Tidak ada header") + joined.count("Tidak ada sinyal kuat")
    return sites_ok, findings


def compute():
    dataset_n, topics = _count_dataset()
    lessons = _count_lessons()
    tools = _count_tools()
    sites_ok, findings = _last_report_stats()

    coding = round(
        100 * (0.5 * min(dataset_n / 500, 1.0) + 0.3 * min(len(topics) / 20, 1.0) + 0.2 * min(len(tools) / 10, 1.0))
    )
    hacking = round(
        100 * (0.5 * min(len(OWASP_COVERED) / 10, 1.0) + 0.3 * min(sites_ok / 5, 1.0) + 0.2 * min(findings / 20, 1.0))
    )
    return {
        "coding_pct": coding,
        "hacking_pct": hacking,
        "dataset_examples": dataset_n,
        "coding_topics_covered": sorted(topics),
        "tools_made": tools,
        "lessons": lessons,
        "owasp_categories_covered": OWASP_COVERED,
        "sites_tested_ok": sites_ok,
        "findings_counted": findings,
    }


if __name__ == "__main__":
    print(json.dumps(compute(), indent=2, ensure_ascii=False))
