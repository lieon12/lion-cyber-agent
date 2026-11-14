# Dataset

Format JSONL, satu contoh per baris:

```json
{"instruction": "...", "input": "...", "output": "..."}
```

- `instruction`: tugas untuk model (tulis kode aman / temukan celah / jelaskan).
- `input`: kode atau pertanyaan.
- `output`: jawaban yang benar — kode aman + penjelasan singkat + referensi (OWASP / CWE).

Kategori awal (53 contoh di `dataset.jsonl`):
SQL injection, XSS, CSRF, broken access control, auth & password hashing,
sensitive data, secure coding umum, pengalaman make.fun (peringkat,
kuota, Force_Last, pelajaran dari 4 ronde food-picture-01), dan
**tool-calling v5 (16 contoh)**: kapan memanggil tool — check_site_basic,
scan_sql, search_web, fetch_url, entry_rank, competition_status,
my_entry_status, list_open_competitions, search_github_tools, vet_tool —
plus 2 contoh merangkum hasil tool. Aturan emas di contoh-contoh itu:
**info live (peringkat, harga, data terbaru) harus dicek lewat tool,
jangan ditebak dari ingatan.**

Batch kedua (60 contoh, 2026-11-14, total 113):
- White-hat / OWASP (20): deteksi + cegah SQLi, XSS (reflected/stored/DOM),
  CSRF, IDOR, akses admin, sesi, HSTS, header Nginx, upload, SSRF,
  path traversal, kebocoran data, debug, XXE, deserialisasi.
- Secure coding (12): login Flask, registrasi, token reset password,
  upload PHP, sesi, JWT, escape HTML, error handling, logging, LIKE aman,
  CSRF PHP, pembatas login.
- Tool-calling (12): check_site_basic, scan_sql, search_web, fetch_url,
  my_entry_status, competition_status, list_open_competitions,
  search_github_tools, read_repo_file, run_self_eval — plus anti-halusinasi
  (info live → panggil tool).
- Cari uang / garapan (8): menilai bounty (food-picture-01, ai-joke-03,
  tiny-chess-01), checklist sebelum ikut, arti 422, syarat klaim,
  cara kerja Scout, membandingkan bounty.
- Belajar mandiri (8): belajar dari internet (search → fetch → rangkum),
  vetting repo GitHub, mengubah kesalahan jadi pelajaran (format
  lessons.md), termasuk pelajaran dari otak lokal v1 yang salah pilih tool.

Target berikutnya: tambah sampai 500-1000 contoh yang bagus, fokus ke
stack website kamu. Kualitas lebih penting dari jumlah.
