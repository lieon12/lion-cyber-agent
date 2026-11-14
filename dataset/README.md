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

Target berikutnya: tambah sampai 500-1000 contoh yang bagus, fokus ke
stack website kamu. Kualitas lebih penting dari jumlah.
