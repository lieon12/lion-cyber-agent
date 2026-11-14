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

Batch ketiga (18 contoh, 2026-11-14, total 131) — perbaikan format
prompt otak lokal: `decide()` di `agent/local_brain.py` sekarang
memakai system prompt yang SAMA PERSIS dengan saat latih (bukan
`system_prompt.md` + daftar tool yang panjang). Contoh baru ini
fokus ke kasus yang gagal: "cek \<URL\>" → check_site_basic dengan
berbagai frasa dan domain yang diizinkan, scan_sql dengan param
realistis (q, username), follow-up "lanjut ..." yang memakai URL
terakhir, entry_rank dengan submission id / handle, dan 3 pertanyaan
konsep yang harus dijawab dengan TEKS (tanpa tool).

Batch keempat (13 contoh, 2026-11-14, total 144) — pelajaran dari
kegagalan latih v2: kenapa output v2 sama persis dengan v1 (mismatch
format prompt), cara memastikan latih ulang benar terpakai (cek
"Jumlah contoh: 131" dan hash adapter), git pull dulu sebelum uji,
open redirect (CWE-601) + ORDER BY allowlist (CWE-89), pelajaran
bounty/Force_Last, dan jangan perbaiki verifydeal.site.

Batch kelima — penalaran, bukan hafalan (18 contoh, 2026-11-15,
total 162). Perintah Lion: "jangan buat dia hanya menghafal tapi
berfikir". Contoh baru ini melatih BERPIKIR dulu baru bertindak:
- Penalaran tool-decision (10): output = 1-3 kalimat penalaran
  singkat (apa yang sebenarnya diminta user, tool mana yang
  menyediakan itu dan kenapa, argumennya apa) BARU JSON tool-call
  di baris sendiri. Melatih membedakan pasangan yang membingungkan:
  check_site_basic vs fetch_url (header/keamanan vs isi halaman),
  check_site_basic vs scan_sql (cek dasar vs uji SQL), search_web vs
  fetch_url (mencari vs membaca), entry_rank vs competition_status
  (peringkat saya vs aturan kompetisi), scan_sql vs search_web.
  Termasuk pelajaran dari kesalahan nyata v3: model mengarang nama
  'check_url' — nama yang benar adalah check_site_basic.
  `parse_tool_call` di `agent/local_brain.py` sudah menerima JSON
  yang dikelilingi teks, jadi format ini jalan tanpa ubah kode.
- Penerapan prinsip (5): cuplikan kode BARU (PHP login SQLi, Flask
  SSTI, Node eval, upload PHP, pickle Python) — output = penalaran
  tentang celahnya (apa, kenapa berbahaya) + kode perbaikannya.
  Bukan tanya-jawab hafalan.
- Penalaran bounty/uang (3): menilai bounty dengan alasan (hadiah,
  deadline, jumlah submission, skill yang dibutuhkan → layak atau
  tidak), memakai hanya fakta terverifikasi: free-model-aggregator-01
  $500, github-core-clone-01 $500 (0 submission saat pertama
  terlihat), coin-launch-01 $1000 — yang terakhir ini BUKAN coding
  biasa: harus launch koin ASLI di pump.fun dengan biaya SOL nyata.

Catatan jujur soal format: 41 contoh tool-calling lama masih
berformat JSON telanjang (tanpa penalaran) dan TIDAK ditulis ulang
— parser menerima kedua format, dan menulis ulang berisiko salah.
Jadi dataset sekarang berisi format campuran; contoh penalaran
yang baru diharapkan mengajari model untuk berpikir dulu, tapi
format campuran berarti model bisa menjawab dengan salah satu
gaya. ~18 contoh penalaran tidak akan membuat model 0.5B menjadi
penalar yang dalam — yang diharapkan adalah generalisasi yang
lebih baik daripada hafalan nama tool.

Panen 1 — ilmu dari pekerjaan nyata (23 contoh, 2026-11-15,
total 185). Perintah Lion: semua yang bokone kerjakan dijadikan
ilmu untuk Kumar. Detail sistem dan isinya ada di
`dataset/HARVEST.md`. Isi panen ini:
- Ringkasan prosa (5): scan_sql tanpa sinyal, Juice Shop 503 → 200,
  testphp tidak terjangkau, rangkuman lab 2026-11-15 — output PROSA,
  bukan JSON (memperbaiki cacat v4: ringkasan keluar sebagai
  {"tool": "report", ...}).
- Git / alur kerja (5): git pull terhalang adapter lokal, membaca
  log latih v4 (162/162, loss 3.993 → 1.909), arti pola loss, urutan
  ganti folder adapter, memastikan otak lokal yang jalan.
- Lab / keamanan (5): 3 header hilang di verifydeal, Juice Shop
  503 → 200 bukan perbaikan, testphp tidak terjangkau, scan_sql
  tanpa sinyal bukan bukti aman, kenapa ringkasan v4 jadi JSON.
- Bounty / uang (5): jendela submit coin-launch-01 (08:00–08:30
  WITA), persiapan aggregator, masuk paling awal github-core-clone,
  token-radar-01 $1325 (pantau), tolak polymarket-faa-attribution-02.
- Prinsip (1): arti "berfikir, bukan menghafal" dalam praktik.
- Keputusan tool dengan penalaran + JSON (2): cek ulang Juice Shop,
  lanjut scan SQL Juice Shop.
