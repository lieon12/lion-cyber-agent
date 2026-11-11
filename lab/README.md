# Laboratorium

Lab ini dijalankan **di mesin bokone**, bukan di Codespace Lion.
Lion tidak perlu menjalankan apa-apa setiap hari — bokone yang
menjalankan kodenya, menulis laporan, lalu push ke repo.

## Cara jalan (di mesin bokone)

```bash
python lab/run_lab.py
```

Hasilnya masuk ke `reports/YYYY-MM-DD.md` dan `reports/YYYY-MM-DD.json`.

## Yang dilakukan lab

Hanya ke target yang diizinkan, payload aman:
- `https://www.verifydeal.site/` — website sendiri
- `http://testphp.vulnweb.com/` — situs uji publik Acunetix, sengaja rentan
- `https://demo.owasp-juice.shop/` — OWASP Juice Shop, sengaja rentan

Per target:
1. `check_site_basic` — HTTPS dan header keamanan
2. `fetch_url` — judul dan isi halaman
3. `scan_sql` param `q` — uji SQL injection non-destruktif

## Otak

Tanpa `GEMINI_API_KEY` di mesin ini, lab berjalan mode rule-based v2
(tools langsung). Kalau API key nanti disediakan untuk mesin ini
lewat Secure Vault (jangan tulis di chat / di file), lab bisa memakai
otak Gemini juga.

## Laporan pagi

Laporan di `reports/` adalah bahan untuk:
- Laporan pagi ke Lion (tool apa yang dibuat, penetrasi apa yang dilakukan, celah apa yang ditemukan)
- Dataset untuk melatih model sendiri nanti
