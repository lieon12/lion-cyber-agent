"""Contoh tool yang ditulis agen sendiri: scanner SQL injection sederhana.

HANYA untuk website milikmu sendiri / yang kamu punya izin tertulis.
Payload non-destruktif saja: tidak ada DROP / DELETE / UPDATE.
Cara pakai:
    python tools/sql_scan.py --url "https://website-kamu.example/login" --param username
"""
import argparse
import difflib
import requests

SAFE_PAYLOADS = [
    "'",
    "' OR '1'='1",
    "' OR 1=1 -- ",
    "' AND 1=2 -- ",
]

ERROR_SIGNS = [
    "sql syntax",
    "mysql",
    "sqlite",
    "postgresql",
    "ora-",
    "unclosed quotation",
    "you have an error in your sql",
]


def test_param(url, param, timeout=10):
    session = requests.Session()
    session.headers.update({"User-Agent": "lion-cyber-agent/0.1 (audit website sendiri)"})
    base = session.get(url, params={param: "test123"}, timeout=timeout)
    findings = []
    for payload in SAFE_PAYLOADS:
        try:
            r = session.get(url, params={param: payload}, timeout=timeout)
        except Exception as e:  # noqa: BLE001
            findings.append({"payload": payload, "error": str(e)})
            continue
        body = r.text.lower()
        ratio = difflib.SequenceMatcher(None, base.text, r.text).ratio()
        hit = [s for s in ERROR_SIGNS if s in body]
        # Respons yang berubah drastis atau memunculkan error DB = sinyal perlu diperiksa manual.
        if hit or ratio < 0.85:
            findings.append(
                {
                    "payload": payload,
                    "status": r.status_code,
                    "similarity_to_baseline": round(ratio, 3),
                    "db_error_signs": hit,
                    "note": "Sinyal kemungkinan rentan — verifikasi manual, jangan simpulkan hanya dari ini.",
                }
            )
    return {"url": url, "param": param, "baseline_status": base.status_code, "findings": findings}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True, help="URL target milikmu sendiri")
    ap.add_argument("--param", required=True, help="Nama parameter yang diuji")
    args = ap.parse_args()
    print(f"Menguji {args.url} param={args.param} (payload aman, non-destruktif)")
    result = test_param(args.url, args.param)
    import json

    print(json.dumps(result, indent=2, ensure_ascii=False))
    if not result["findings"]:
        print("\nTidak ada sinyal kuat. Bukan berarti 100% aman — lanjutkan audit kode.")
    else:
        print("\nAda sinyal. Periksa kode: pakai prepared statement / parameter binding.")


if __name__ == "__main__":
    main()
