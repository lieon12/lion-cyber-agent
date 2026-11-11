"""Laboratorium lion-cyber-agent — dijalankan di mesin bokone, bukan di Codespace Lion.

Cara jalan:
    python lab/run_lab.py [--date 2026-11-11]

Yang dilakukan (hanya ke target yang diizinkan, payload aman):
1. check_site_basic ke setiap target
2. fetch_url ke setiap target
3. scan_sql param=q ke setiap target
4. Tulis laporan ke reports/YYYY-MM-DD.md + reports/YYYY-MM-DD.json

Target yang diizinkan (lihat agent/validator.py):
- https://www.verifydeal.site/ — website sendiri
- http://testphp.vulnweb.com/ — situs uji publik Acunetix, sengaja rentan
- https://demo.owasp-juice.shop/ — OWASP Juice Shop, sengaja rentan

Kalau satu target tidak bisa dijangkau, lab mencatat kegagalannya dan
lanjut ke target berikutnya, bukan berhenti total.

Tanpa GEMINI_API_KEY di mesin ini, lab berjalan mode rule-based v2
(tools langsung, tanpa otak Gemini). Jangan pernah tulis API key
di file ini atau di laporan.
"""
import argparse
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agent.agent import run  # noqa: E402
from agent.capabilities import compute as compute_capabilities  # noqa: E402

TARGETS = [
    "https://www.verifydeal.site/",
    "http://testphp.vulnweb.com/",
    "https://demo.owasp-juice.shop/",
]


def summarize_trace(trace):
    findings = []
    for step in trace:
        if not step["ok"]:
            findings.append(f"Tool {step['tool']} gagal: {step.get('error')}")
            continue
        r = step["result"]
        if step["tool"] == "check_site_basic":
            findings.append(f"check_site_basic: status {r.get('status')}")
            for f in r.get("findings", []):
                findings.append(f"  * {f}")
        elif step["tool"] == "fetch_url":
            findings.append(f"fetch_url: {r.get('title')} (status {r.get('status')}, server {r.get('server')})")
        elif step["tool"] == "scan_sql":
            findings.append(
                f"scan_sql: {r.get('url')} param={r.get('param')} (baseline status {r.get('baseline_status')})"
            )
            if not r.get("findings"):
                findings.append("  * Tidak ada sinyal kuat. Bukan berarti 100% aman — lanjutkan audit kode.")
            for f in r.get("findings", []):
                findings.append(f"  * payload {f.get('payload')!r}: status {f.get('status')}")
    return findings


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=date.today().isoformat())
    args = parser.parse_args()

    all_trace = []
    per_target = {}
    for target in TARGETS:
        trace = []
        last_url = None
        for task in [f"cek {target}", "lanjut scan SQL-nya"]:
            for step in run(task, last_url=last_url):
                trace.append(step)
                if step["ok"] and isinstance(step.get("result"), dict) and step["result"].get("url"):
                    last_url = step["result"]["url"]
        per_target[target] = summarize_trace(trace)
        all_trace.extend(trace)

    reports = ROOT / "reports"
    reports.mkdir(exist_ok=True)
    # Hitung kemampuan dulu berdasarkan laporan terakhir, lalu simpan
    # laporan baru — jadi persen di laporan ini adalah dari laporan
    # sebelumnya, dan akan naik di laporan besok kalau ada kemajuan.
    caps = compute_capabilities()
    data = {
        "date": args.date,
        "targets": TARGETS,
        "tools_used": sorted({s["tool"] for s in all_trace}),
        "per_target": per_target,
        "trace": all_trace,
        "capabilities": caps,
    }
    (reports / f"{args.date}.json").write_text(
        json.dumps(data, indent=2, ensure_ascii=False, default=str), encoding="utf-8"
    )
    lines = [
        f"# Laporan Lab — {args.date}",
        "",
        "Target yang diizinkan: " + ", ".join(TARGETS),
        f"Tools dipakai: {', '.join(data['tools_used'])}",
        "",
    ]
    for target, findings in per_target.items():
        lines += [f"## {target}", ""]
        lines += [f"- {f}" for f in findings]
        lines += [""]
    lines += [
        "## Kemampuan agen (perkiraan dari cakupan, bukan nilai ujian)",
        "",
        f"- Coding: {caps['coding_pct']}% — dataset {caps['dataset_examples']} contoh, "
        f"topik {len(caps['coding_topics_covered'])}/20, tool {len(caps['tools_made'])}/10",
        f"- Hacking / cari celah: {caps['hacking_pct']}% — kategori OWASP {len(caps['owasp_categories_covered'])}/10, "
        f"situs berhasil diuji {caps['sites_tested_ok']}/5, temuan {caps['findings_counted']}/20",
        "",
        "### Kemampuan yang sudah ada",
        "",
        "- Ngobrol lewat chat (`python -m agent.chat`), ingat pelajaran, koreksi dengan 'itu salah'",
        "- Otak Gemini (kalau API key ada) atau fallback rule-based",
        "- Validator: hanya tool, domain, dan payload yang diizinkan yang boleh jalan",
        "",
        "### Tools yang sudah dibuat",
        "",
    ]
    lines += [f"- {t}" for t in caps["tools_made"]]
    lines += [
        "- tools/sql_scan.py — scanner SQL injection (payload aman)",
        "",
        "Cara hitung persen ada di `agent/capabilities.py`. Persen naik kalau "
        "dataset, tool, dan temuan bertambah.",
        "",
        "## Catatan",
        "",
        "- Scan memakai payload non-destruktif saja.",
        "- 'Tidak ada sinyal kuat' bukan berarti 100% aman — lanjutkan audit kode.",
        "- Data di laporan ini (temuan + pelajaran) adalah bahan untuk melatih model sendiri nanti.",
        "",
    ]
    (reports / f"{args.date}.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Lab selesai. Laporan: reports/{args.date}.md")
    for target, findings in per_target.items():
        print(f"\n== {target} ==")
        for f in findings:
            print(f)


if __name__ == "__main__":
    main()
