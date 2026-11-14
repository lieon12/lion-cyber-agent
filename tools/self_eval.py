"""Evaluasi diri Kumar: uji tool-nya sendiri ke target yang diizinkan, lalu nilai.

Kumar menjalankan check_site_basic dan scan_sql ke target yang
diizinkan, lalu membandingkan hasilnya dengan temuan yang SUDAH
diketahui dari lab — jadi nilainya dihitung dari kenyataan, bukan
dari perkiraan. Skor ini TERPISAH dari persen Coding/Hacking di
agent/capabilities.py (file itu tidak diubah).

Hanya ke target yang diizinkan (website sendiri + situs uji publik),
payload non-destruktif saja. Target yang tidak bisa dijangkau dicatat
sebagai "unreachable" — hasilnya tidak pernah dikarang.

Temuan yang diharapkan (dari laporan lab 2026-11-11 s/d 2026-11-14):
- verifydeal.site: status 200, HSTS ada, CSP / X-Frame-Options /
  X-Content-Type-Options hilang; scan SQL param q: baseline 200,
  tidak ada sinyal kuat.
- demo.owasp-juice.shop: status 200, HSTS dan CSP hilang.
- testphp.vulnweb.com: dari mesin lab tidak bisa dijangkau (proxy) —
  kalau tiba-tiba bisa, yang diharapkan status 200.

Hasil ditulis ke reports/self-eval-latest.json (seperti laporan lab).
"""
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

TARGETS = [
    "https://www.verifydeal.site/",
    "https://demo.owasp-juice.shop/",
    "http://testphp.vulnweb.com/",
]

# check: (nama, cara nilai hasil check_site_basic)
# Nilai "expected" ditulis apa adanya; "actual" diisi dari hasil live.
SITE_CHECKS = {
    "https://www.verifydeal.site/": [
        ("status_200", lambda r: r.get("status") == 200),
        ("hsts_present", lambda r: bool((r.get("security_headers") or {}).get("Strict-Transport-Security"))),
        ("csp_missing", lambda r: not (r.get("security_headers") or {}).get("Content-Security-Policy")),
        ("xfo_missing", lambda r: not (r.get("security_headers") or {}).get("X-Frame-Options")),
        ("xcto_missing", lambda r: not (r.get("security_headers") or {}).get("X-Content-Type-Options")),
    ],
    "https://demo.owasp-juice.shop/": [
        ("status_200", lambda r: r.get("status") == 200),
        ("hsts_missing", lambda r: not (r.get("security_headers") or {}).get("Strict-Transport-Security")),
        ("csp_missing", lambda r: not (r.get("security_headers") or {}).get("Content-Security-Policy")),
    ],
    "http://testphp.vulnweb.com/": [
        ("status_200", lambda r: r.get("status") == 200),
    ],
}

SQL_TARGET = "https://www.verifydeal.site/"
SQL_PARAM = "q"


def _check(name, fn, result):
    try:
        ok = bool(fn(result))
    except Exception:
        ok = False
    return {"name": name, "passed": ok}


def run_self_eval():
    """Jalankan evaluasi diri. Kembalikan dict hasil + tulis JSON-nya.

    Struktur hasil: date, score_pct (None kalau tidak ada target yang
    bisa dijangkau), passed_checks, total_checks, unreachable (list),
    targets: {url: {status, passed, total, checks: [{name, passed}]}}.
    """
    # Import di sini (bukan di atas) supaya tidak circular: agent/tools.py
    # memuat modul ini, jadi agent.tools baru bisa diimpor setelah itu selesai.
    from agent.tools import check_site_basic, scan_sql

    targets = {}
    passed_total = 0
    total = 0
    unreachable = []

    for url in TARGETS:
        entry = {"target": url, "status": "ok", "passed": 0, "total": 0, "checks": []}
        try:
            basic = check_site_basic(url)
        except Exception as e:  # noqa: BLE001 - target tidak bisa dijangkau, catat jujur
            entry["status"] = "unreachable"
            entry["error"] = str(e)[:300]
            unreachable.append(url)
            targets[url] = entry
            continue
        for name, fn in SITE_CHECKS.get(url, []):
            c = _check(name, fn, basic)
            entry["checks"].append(c)
            entry["total"] += 1
            total += 1
            if c["passed"]:
                entry["passed"] += 1
                passed_total += 1
        targets[url] = entry

    # Scan SQL di verifydeal.site — hanya kalau situsnya bisa dijangkau.
    sql_entry = {"target": SQL_TARGET, "param": SQL_PARAM, "status": "ok", "passed": 0, "total": 0, "checks": []}
    if targets.get(SQL_TARGET, {}).get("status") == "ok":
        try:
            res = scan_sql(SQL_TARGET, param=SQL_PARAM)
            for name, ok in [
                ("baseline_200", res.get("baseline_status") == 200),
                ("no_strong_signal", not res.get("findings")),
            ]:
                sql_entry["checks"].append({"name": name, "passed": bool(ok)})
                sql_entry["total"] += 1
                total += 1
                if ok:
                    sql_entry["passed"] += 1
                    passed_total += 1
        except Exception as e:  # noqa: BLE001
            sql_entry["status"] = "error"
            sql_entry["error"] = str(e)[:300]
    else:
        sql_entry["status"] = "skipped_unreachable"
    targets["sql_scan:" + SQL_TARGET] = sql_entry

    score = round(100 * passed_total / total) if total else None
    record = {
        "date": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "score_pct": score,
        "passed_checks": passed_total,
        "total_checks": total,
        "unreachable": unreachable,
        "targets": targets,
        "note": (
            "Skor evaluasi diri ini terpisah dari persen Coding/Hacking "
            "di agent/capabilities.py. 'Tidak ada sinyal kuat' bukan berarti aman."
        ),
    }
    out = ROOT / "reports" / "self-eval-latest.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    return record


if __name__ == "__main__":
    print(json.dumps(run_self_eval(), indent=2, ensure_ascii=False))
