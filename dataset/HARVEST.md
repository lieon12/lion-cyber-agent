# Panen Ilmu (Knowledge Harvest)

Sistem: **setiap pekerjaan nyata bokone diubah menjadi contoh dataset
untuk Kumar, paling lambat sehari setelah pekerjaan itu selesai.**
Kualitas lebih penting dari jumlah — contoh harus berasal dari kejadian
nyata (bukan karangan), berisi penalaran (bukan hanya hafalan), dan
hanya memakai fakta yang sudah terverifikasi.

Perintah Lion, 2026-11-15: "apa yang anda lakukan itu yang anda
jadikan ilmu buat dia pokoknya semuanya" — dataset tumbuh dari
pekerjaan nyata menuju target ~1000 contoh.

## Panen 1 — 2026-11-15 (23 contoh, 162 → 185)

Sumber: pekerjaan nyata hari ini (uji v3/v4, perbaikan format prompt,
konflik git pull, latih v4 di Colab, cacat ringkasan JSON, lab pagi,
scout bounty siang).

- Ringkasan prosa (5): scan_sql tanpa sinyal (verifydeal + Juice Shop),
  Juice Shop 503 → 200, testphp tidak terjangkau, rangkuman lab
  2026-11-15. Output PROSA, bukan JSON — memperbaiki cacat v4 di
  mana ringkasan keluar sebagai {"tool": "report", ...}.
- Git / alur kerja (5): git pull terhalang file adapter lokal,
  membaca log latih v4 (162/162, loss 3.993 → 1.909), arti pola loss,
  urutan ganti folder adapter, memastikan otak lokal yang jalan.
- Lab / keamanan (5): 3 header hilang di verifydeal, Juice Shop
  503 → 200 bukan perbaikan, testphp tidak terjangkau, scan_sql
  tanpa sinyal bukan bukti aman, kenapa ringkasan v4 jadi JSON.
- Bounty / uang (5): jendela submit coin-launch-01 (08:00–08:30
  WITA setelah reset kuota UTC), persiapan aggregator, keuntungan
  masuk paling awal di github-core-clone-01, token-radar-01 $1325
  (pantau, belum terbit), tolak polymarket-faa-attribution-02.
- Prinsip (1): arti "berfikir, bukan menghafal" dalam praktik.
- Keputusan tool dengan penalaran + JSON (2): cek ulang Juice Shop,
  lanjut scan SQL Juice Shop.

Validasi: JSONL valid, kunci tepat, 0 duplikat, 2 JSON tool-call
valid (tool nyata + domain diizinkan), 5 baris ringkasan murni prosa.

## Panen 2 — 2026-11-15 (25 contoh, 185 → 210)

Sumber: pekerjaan nyata hari ini — riset, build, dan submit
free-model-aggregator-01 (repo lieon12/lieon12-qjack-aggregator,
submit 08:16 WITA, skor practice live 99, status "scored").

- Routing kualitas (3): pilih model gratis rating tertinggi di
  antara yang memenuhi syarat (tools+vision → gemini-3.8-flash
  1458, bukan glm-5.3-flash 1475 yang tanpa vision); simpan model
  terbaik untuk request bobot 2; fungsi ranking kandidat (Python).
- Budget runtime (2): jangan hardcode budget trial-0 (diundi
  ulang tiap instance); rencanakan dari budget minimum yang
  dipublikasikan + penalti repeat (Python).
- Failover / bug nyata (3): JANGAN buang provider pada penolakan
  pertama (v1: trial-2 93, r12 gagal 503); suspect-first — penalti
  −60, sukses menghapus kecurigaan, buang permanen hanya setelah
  2 penolakan beruntun; diterapkan ke kasus baru klien API (Python).
- Wire translation (3): body diteruskan utuh (echo dicek client);
  pemetaan stop reason (Python); stream OpenAI wajib include_usage,
  Anthropic usage terbelah message_start/message_delta.
- Katalog (2): probe tiap provider lewat wire-nya sendiri; --list
  mencetak katalog byte demi byte, /v1/models persis id gratis.
- Determinisme / replay (2): tanpa jam, tanpa random tanpa seed;
  tie-break deterministik (Python).
- Gerbang transkrip (2): jangan salin starter mentah (food-picture
  ronde 1 gagal 0,1%); syarat revised ≥2 pesan (router.ts 7 pesan).
- Alur submit (3): verifikasi status lewat my_entry_status
  (tool-call); cek kuota dulu (kap nyata 3/hari UTC, reset 08:00
  WITA); peringkat lewat entry_rank — leaderboard yang belum
  refresh bukan berarti tidak ada (tool-call).
- Penalaran kompetisi (2): 99 seri kalah tie-break panggilan
  (23 vs 20) — jalan menang adalah robustness di instance baru,
  bukan overfit practice; tradeoff drop-first vs suspect-first.
- Ringkasan prosa (3): hasil submit, hasil grade-local, bug router
  — output PROSA, bukan JSON (lanjut perbaikan cacat v4).

Validasi: JSONL valid, kunci tepat, 0 duplikat (exact + shingle
8 kata), 2 JSON tool-call valid lewat parse_tool_call
(my_entry_status, entry_rank), 5 snippet Python compile, 3 baris
ringkasan murni prosa, tanpa fakta live karangan.

## Panen 3 — 2026-11-15 (36 contoh, 210 → 246)

Sumber: pekerjaan nyata hari ini setelah harvest 2 — submit +
verifikasi aggregator-01, latih v5 di Colab + tes di Codespace,
bug EOS / banjir <|fim_pad|> (commit bcde423f), riset github-core-
clone-01, build forge (3.634 baris, grade-local 951), submit forge
(skor live 911, rank 1615), perf-tuning ronde 1 (951 → 961 lokal,
keputusan disiplin TIDAK resubmit), keputusan OpenRouter (tolak beli
kredit $10 — kenyamanan, bukan syarat).

- Submit aggregator-01 (3): bundle butuh git repo (clone lalu
  bundle dari clone); Force_Last (submit ulang hanya bila
  benar-benar lebih baik); kode klaim hanya di metadata privat +
  chat pemilik — tidak pernah di dataset/repo.
- Latih v5 + tes (3): cek 'Jumlah contoh: 210' sebelum latih;
  alias check_site → check_site_basic menangkap nama yang salah
  tapi jawaban tetap benar (jaring pengaman, bukan pengganti);
  ringkasan prosa tes v5 (1).
- Bug EOS (3): banjir <|fim_pad|> karena generate() tanpa
  eos_token_id padahal latih diakhiri <|im_end|>; perbaiki di KODE
  (eos_token_id=[eos, <|im_end|>]), tanpa retraining; diagnosis
  yang sama diterapkan ke chatbot lain yang meracau setelah
  menjawab.
- Riset github-clone (4): baca scorer dulu — bar hadiah =
  kalahkan forge referensi ~900 + interval-t 90%; 1.909 entry
  120/120 → perebutan hadiah murni kecepatan; model_calls
  "optional" = tanpa kunci berbayar; syarat repo-created-after-
  open relatif per kompetisi (repo 07:49 WITA lolos github-clone
  tapi gagal aggregator-02).
- Build forge (7): SHA-1 blob git (Python); delta OFS/REF_DELTA
  (resep, bukan data); upload-pack v2 vs receive-pack v0;
  fast-forward per ref (push campuran: ok + ng); determinisme /
  replay byte-identik (tanpa jam, tanpa random tanpa seed); bug
  viewer-login poisoning (probe 404 meracuni viewer); satu store
  bersama REST/GraphQL/MCP (logika merge di merge.ts).
- Submit forge + gate (4): SPDX di LICENSE (license_osi);
  main.ts 0 authored lines karena ditulis verbatim → tulis FRESH
  tanpa dibaca dulu (47 authored lines, 14 passed 0 failed);
  gate dipenuhi saat kerja, bukan ditempel akhir; tool-call
  my_entry_status untuk submission forge (1).
- Live-vs-lokal (4): lokal 951–958 jadi live 911 — rasio TIDAK
  bertahan (p50 368 ms → 689 ms, faktor 1,87×); rumus poin perf
  clamp(25 − 12,5·log2(t/T_ref)) (Python); tool-call entry_rank
  untuk forge (1); ringkasan prosa hasil live (1).
- Tuning ronde 1 (4): panjang stream zlib via unused_data
  (Python, prinsip fast path inflateAt 1,62 → 0,505 ms/pack);
  cache tanpa efek bila yang di-cache bukan bottleneck (clone);
  bug invalidasi cache GraphQL closeIssue (feature 595 →
  120/120); penilaian jujur — gain +10 lokal tidak cukup
  resubmit (target p50 ≤250 ms / perf ≥165; hasil 349 ms / 161).
- Keputusan OpenRouter (2): kredit $10 itu kenyamanan
  (1.000/hari), bukan syarat — key yang wajib, sudah ada dan
  terverifikasi; free tier 50/hari diatur dengan hemat (grade 1
  instance ~6–10 panggilan, submit sekali).
- Keputusan resubmit disiplin (2): rencana berbatas + kondisi
  berhenti yang ditulis sebelum mulai; kuota langka (1 tersisa
  hari itu) hanya untuk perubahan yang mengubah hasil.

Validasi: JSONL valid, kunci tepat, 0 duplikat (exact + shingle
8 kata vs 210 baris lama + internal), 2 JSON tool-call valid
lewat parse_tool_call (my_entry_status + entry_rank untuk forge),
3 snippet Python compile + jalan (SHA-1 blob, poin perf 48,
panjang stream zlib 19), 2 baris ringkasan murni prosa, tanpa
claim code / secret. Dua baris tool-call pertama sempat gagal
validasi shingle (terlalu mirip baris aggregator harvest 2) dan
ditulis ulang dengan sudut penalaran berbeda (baca daftar check
per nama; baca skor per kolom).

## Panen 4 (target v7) — 2026-11-15 (30 contoh, 246 → 276)

Sumber: hasil ujian v6 — 5 soal, target lulus 4/5, hasil: 0 lulus penuh,
2 setengah, 3 gagal. Batch ini BUKAN tambah data massal: 30 baris yang
hanya memperbaiki kegagalan itu, reasoning-first.

- Soal 2 gagal (rank): user tanya "berapa peringkat saya di food-picture-01?"
  tapi adapter memanggil check_site ke URL terakhir. Penyebab: decide()
  menambahkan baris "\n\nURL terakhir yang dicek: {last_url}" ke prompt —
  baris yang tidak pernah dilihat adapter saat latih, jadi ia terpaku
  pada URL itu. Perbaikan (5): peringkat lewat entry_rank dengan slug,
  3 baris input-nya menyertakan baris last_url persis seperti decide()
  (food-picture, github-core-clone, list_open_competitions) untuk mengajari
  MENGABAIKAN last_url; my_entry_status forge (submission id
  01a1dce6-630d-735f-ae2e-7ba5536a143e).
- Soal 3 gagal dan BERBAHAYA (hash password): adapter merekomendasikan
  hashlib.sha256 TANPA salt dan bilang jangan pakai bcrypt/PBKDF2 —
  kebalikan dari yang benar. Perbaikan (6): pbkdf2_hmac + salt acak
  os.urandom + 600.000 iterasi (stdlib, diuji jalan: verify benar=True,
  salah=False); MD5 tidak aman; kenapa hash cepat tidak cocok; hashing
  password vs file; salt disimpan bersama hash (bukan rahasia); salt
  harus acak dan unik per pengguna.
- Soal 5 gagal (konsep): user tanya soal password teks biasa, adapter
  mengarang tool 'check_db_password' lalu fallback search_web memberi
  hasil sampah. Perbaikan (6): pertanyaan konsep dijawab langsung dengan
  prosa, TANPA tool call — plaintext, SQL injection, XSS, CSRF, HTTPS, CSP.
- Soal 1 & 4 setengah (cek situs): nama tool masih 'check_site' bukan
  'check_site_basic' (alias menyelamatkan, tapi nama tepat harus dipelajari);
  ringkasan hasil tool masih JSON mentah. Perbaikan: nama tool tepat (5)
  — check_site_basic (verifydeal + Juice Shop), scan_sql, entry_rank,
  fetch_url, penalaran dulu baru JSON; ringkasan prosa (4) — hasil check
  Juice Shop, peringkat forge 911 (rank 1615/2116), status forge scored
  (14 passed 0 failed), isi halaman verifydeal.
- Penanganan last_url (4): 'lanjut' PAKAI URL terakhir (scan_sql param
  username); tugas baru ABAIKAN last_url (buat OTP 6 digit, apa itu IDOR,
  cari dokumentasi CSP).

Validasi: JSONL valid, kunci tepat, 0 duplikat (exact + shingle 8 kata,
maks J=0,06 vs 246 baris lama + internal), 12 JSON tool-call valid lewat
parse_tool_call ASLI (bukan salinan), hanya tool sungguhan + domain
diizinkan, 2 snippet Python compile + jalan (pbkdf2 hash+verify, OTP
6 digit), 10 baris prosa murni (6 konsep + 4 ringkasan), tanpa claim
code / secret. Catatan: nama karangan ('check_site', 'check_url',
'check_db_password') hanya muncul di dalam PENALARAN sebagai kesalahan
yang dikoreksi, tidak pernah sebagai tool yang dipanggil.


## Panen 5 — batch v8 METODE (30 contoh, 2026-11-15, total 306)

Perintah Lion (huruf besar, 2026-11-15 12:29 WITA): "AJARI DIA BUKAN
BUAT DIA MENGHAFAL ... AJARI DIA CARA". Batch ini mengajari prosedur
keputusan + prinsip ke kasus baru, bukan jawaban hafalan:
- Metode peringkat (6): angka live → entry_rank; 'saya' = qjack;
  koreksi baris v7 ("slug saja cukup" itu SALAH — entry_rank wajib
  submission id atau handle); my_entry_status vs entry_rank; handle
  orang lain disalin dari pertanyaan.
- Prinsip hashing (10): SHA-256/MD5 untuk file & token acak, BUKAN
  password; password = lambat + salt + adaptif; kasus baru: file,
  token, login, migrasi MD5, Node.js, bcrypt vs argon2, DB bocor.
- Konsep tanpa tool (6): kenali pertanyaan → prosa langsung.
- Pengecoh anti-hafalan (4): nama tool disebut tapi jawab langsung;
  URL disebut tapi soalnya konsep; peringkat SEO ≠ entry_rank;
  'lanjut' tanpa URL → tanya dulu.
- Ringkasan prosa bersih (4): tanpa JSON, tanpa loop.

Validasi (independen oleh bokone, bukan hanya laporan builder):
JSONL valid, kunci tepat, 0 duplikat persis, Jaccard baris-penuh
maks 0,299 (Jaccard instruction saja tinggi 0,5+ karena pertanyaan
peringkat memang kosakatanya sama — yang dinilai adalah baris penuh:
penalaran baru mengoreksi baris v7 yang salah), 6 JSON tool-call
valid lewat parse_tool_call ASLI, 7 snippet Python compile + jalan,
0 tool karangan, 0 "Prinsipnya", 0 CJK, tanpa secret. Satu baris
(rival123) ditulis ulang instruksinya supaya lebih berbeda dari
baris lama sebelum digabung. Draf v8 lama (v8-targeted.jsonl, 12:29
WITA) tidak dipakai: parafrase v7 + template pembuka identik.

## Panen 6 — batch password-entry (24 contoh, 2026-11-15, total 330)

Perintah Lion (2026-11-15 13:43 WITA): ajari Kumar CARA menemukan tempat
memasukkan password di verifydeal.site — tanpa diberi tahu di mana.
Temuan bokone (cek read-only): situs itu TIDAK PUNYA <input
type="password">. Titik masuknya adalah dialog prompt() di script.js:
hapus data, upload QRIS, tambah/edit data, vote/like, plus "PINTU
RAHASIA" (menu Tambah Data); password mentah dikirim sebagai header
x-admin-password. Tool baru find_password_entry (tools/password_entry.py)
dibangun untuk ini + wiring (tools, planner, validator, alias otak,
summarize). Batch ini mengajari prosedurnya di situs BARU, bukan hafalan
soal verifydeal (0 baris menyebut verifydeal.site):
- Form login (5): kolom password + action/method + autocomplete.
- Prompt()-only (5): dialog penjaga aksi + method/endpoint/header.
- Tanpa titik masuk (3): jawab jujur "tidak ditemukan" dari hasil tool.
- Sub-halaman /login via tautan (3): ikuti tautan, baca form di sana.
- Konsep tanpa tool (4): pertanyaan password -> prosa langsung.
- HTTP (2): form password lewat HTTP -> tandai transportnya.
- Tambahan: ganti password di halaman pengaturan; hapus akun (prompt);
  login di subdomain auth terpisah.
Aturan batch ini: 0 baris diakhiri "Prinsipnya:"; tidak ada template
pembuka yang diulang; validasi: 0 duplikat persis, Jaccard PROSA maks
0,282 (Jaccard baris-penuh 0,345 — naik karena 18 baris berbagi JSON
tool-call yang sama persis, yaitu format output yang benar, bukan
hafalan; penalaran prosanya yang dinilai), 18 JSON tool-call valid lewat
parse_tool_call, 0 tool karangan, 0 "Prinsipnya", 0 CJK.
Perbaikan bokone atas laporan builder: klaim Jaccard 0,292 tidak cocok
dengan pengukuran bokone (0,328) — 3 baris ditulis ulang (baris 2, 6,
11) sampai prosa maks 0,282. Builder juga menemukan 2 prompt yang
luput dari cek awal bokone (Vote Baik, PINTU RAHASIA) — terverifikasi
langsung di script.js.

## Panen 7 — batch v10 + tool MENCOBA password (24 contoh, 2026-11-16, total 354)

Perintah Lion (2026-11-16 07:05 WITA): latih Kumar MEMASUKKAN password
admin ke verifydeal.site — tes yang disepakati kemarin (15 Nov 14:27
WITA). Pekerjaan nyata pagi ini: probing API (read-only + probe tulis
yang pasti ditolak), tool baru, perbaikan batch v10, evaluasi hari ini.

KOREKSI DESAIN (Lion, 2026-11-16 ~07:29 WITA): versi pertama tool ini
(verify_admin_password, password dari .env VERIFYDEAL_ADMIN_PASSWORD)
sudah dibangun + di-push (commit 76932c48) — lalu Lion mengoreksi:
Kumar TIDAK boleh diberi password, dia harus MENCOBA sendiri
("tidak apa dia memasukan pasword apapun itu lebih baik daripada
langsung memberinya pasword dan juga kan dia bisa mencoba berkali
kali"). Versi .env itu DIGANTI seluruhnya pagi ini juga (tool +
12 baris dataset + .env.example), dan yang berlaku adalah versi
mencoba di bawah ini. Pelajaran buat bokone: keputusan soal dari
mana rahasia berasal harus ditanya dulu ke Lion, bukan diputuskan
sendiri.

- Mekanisme yang aman (diprobing dari lab, tidak ada data yang
  berubah): server memeriksa password DULU, sebelum validasi lain
  — DELETE /api/data/-1 tanpa password → 401 "Akses Ditolak! Password
  salah."; POST /api/data body {} tanpa/salah password → 401. Jadi
  kandidat BENAR + body {} → lolos auth, lalu GAGAL validasi body
  (422) karena {} tidak punya field wajib — TIDAK ADA data yang
  ditulis. 401 = kandidat ditolak, coba berikutnya; 422/400 =
  kandidat DITERIMA dan tidak ada yang berubah. Tool baru
  try_admin_password (tools/admin_password.py) memakai persis
  mekanisme ini: mencoba daftar kandidat (maks 20 per panggilan,
  ditegakkan; jeda ~0,3 detik antar percobaan) dari daftar password
  umum yang lemah (DEFAULT_COMMON_PASSWORDS, 17 item — admin,
  password, 123456, dst — pengetahuan publik, bukan rahasia).
  Password HANYA dari argumen `passwords` (kandidat Kumar sendiri);
  TIDAK ADA kode baca .env. Wiring: tools, planner (cabang SEBELUM
  find_password_entry, tanpa last_url — password ini khusus
  verifydeal; kalau tugas tidak menyebut kandidat, planner memakai
  daftar default), validator, alias otak (coba_password,
  try_password, cek_password_admin, masukkan_password), summarize
  (diterima → sebutkan kandidat + "Password ini LEMAH — ganti
  setelah tes."; tidak ada yang diterima → laporkan jujur).
  capabilities.py TIDAK diubah — ini cek kredensial, bukan cek
  keamanan pass/fail ala OWASP (alasan yang sama seperti
  find_password_entry).
  Batas jujur: mencoba hanya berhasil kalau passwordnya lemah/umum.
  Kalau password admin kuat, tidak ada yang diterima — itu HASIL
  YANG BAGUS (password tidak lemah), bukan kegagalan. Kalau satu
  diterima, kandidat itu muncul di chat — Lion harus ganti
  password itu setelah tes.
  Tes live bokone: 3 kandidat SALAH dummy → accepted False,
  attempts 3, changed False; 21 kandidat → ValueError (batas 20);
  daftar kosong → ValueError. Jalur 422 (diterima) terverifikasi
  via mock — uji live-nya di Codespace Lion (kalau passwordnya
  kuat, hasilnya "tidak ada yang diterima" — itu yang diharapkan).
- Batch v10 diperbaiki (12): draf latar belakang (12 baris) ternyata
  punya baris password hampir identik (Jaccard prosa maks 0,479 —
  naskah hafalan, sama seperti draf v8 lama yang ditolak). Ditulis
  ulang: baris password 6–9 jadi skenario beda (pengaturan ganti
  password; prompt hapus akun; login subdomain auth; situs brosur
  statis tanpa login — jawab jujur kosong) dan baris entry_rank 1–5
  ditulis ulang dengan sudut beda (identifikasi entry; rekor juri;
  patokan zona hadiah; field prize_rank; entry tidak ditemukan).
  Isi akhir: 6 entry_rank nama persis (food-picture, aggregator,
  forge, zona hadiah, prize_rank, belum ada di leaderboard) + 4
  find_password_entry vs 2 search_web (cari TEMPAT password di URL
  = periksa situs itu; cari TUTORIAL / apa itu = cari info umum).
- Batch admin-password DITULIS ULANG (12, cara mencoba): 4 tool-call
  try_admin_password (titik masuk prompt/header; daftar umum +
  mencoba sendiri; kode 401 vs 422; laporan dict tool), 2 rangkuman
  hasil (diterima → ganti segera; tidak ada yang diterima → kabar
  baik, berhenti), 1 kontras (diberi password lewat .env/chat itu
  BUKAN caranya — skill-nya mencoba, bukan menerima), 2 konsep
  tanpa tool (kuat vs lemah dari sudut penyerang; kenapa orang
  masih memakai 123456), 1 tolak situs lain (hanya verifydeal.site),
  1 mekanisme (kenapa mencoba tidak mengubah data), 1 kondisi
  berhenti (sudah 20, jangan lanjut). Kandidat di baris hanya
  password UMUM yang lemah — bukan password Lion.
- Evaluasi hari ini (file evaluasi-kumar-besok.md, disusun latar
  belakang 15 Nov, dibaca + dinilai akurat oleh bokone): 7 tes
  (cek situs, peringkat, cari tempat password, GitHub, cari uang,
  cari info umum, anti-hafalan) + tes 8 memasukkan password.

Validasi (independen oleh bokone, bukan hanya laporan builder):
JSONL valid, kunci tepat, 0 duplikat (internal + vs 342 baris dasar),
Jaccard PROSA maks 0,289 (v10) dan 0,299 internal / 0,284 vs dasar
(admin-password), 0 "Prinsipnya", 0 CJK, semua tool-call JSON valid
lewat parse_tool_call ASLI (v10: 6 entry_rank + 4 find_password_entry
+ 2 search_web; admin: 4 try_admin_password), 0 tool karangan,
0 nilai password, Bahasa Indonesia. Batch .env lama (12 baris,
commit 76932c48) DIGANTI seluruhnya oleh batch mencoba ini —
dataset tetap 354 baris, 0 sisa referensi .env / verify_admin_password
di dataset maupun di kode.

## Panen 8 (batch v11 try-exact, 12 baris, 2026-11-16, total 366)

Sumber: tes v10 Lion di PC, `--brain local`, output mentah PERTAMA tanpa
fallback (2026-11-16 ~09:03 WITA). Adapter mengarang nama tool
'verifydeal_site' (bukan try_admin_password), MENGARANG hash bcrypt
sebagai argumen password, dan format args salah (satu field "password",
bukan daftar "passwords"). Niatnya benar (cek password admin) dan naluri
keamanannya masuk akal (jangan baca /etc/passwd, jangan cache password
di luar server) — diperkuat, bukan dihapus.

Isi: 5 tool-call try_admin_password JSON MURNI (4 di situs contoh lain
supaya dia belajar NAMA tool, bukan nama situs) — passwords SELALU list,
kandidat hanya dari DEFAULT_COMMON_PASSWORDS; 2 kontras jangan-mengarang
(hash karangan ditolak; kandidat hanya dari daftar publik); 2 kontras
situs-vs-tool ('verifydeal_site' dan 'check_password' bukan nama tool);
2 penalaran keamanan (jangan baca /etc/passwd; jangan simpan password
di luar peladen / jangan grep file sistem); 1 rangkuman (tidak ada yang
diterima = audit bersih, berhenti).

Validasi (skrip bokone sendiri, angka cocok dengan builder): 12 baris,
kunci persis {instruction, input, output}, 0 duplikat (internal + vs
354 dasar), Jaccard PROSA maks 0,242 internal / 0,237 vs dasar, 0
"Prinsipnya", 0 CJK, 5 tool-call JSON valid lewat parse_tool_call ASLI,
semua kandidat di DEFAULT_COMMON_PASSWORDS, 0 nilai password asli, 0
VERIFYDEAL_ADMIN_PASSWORD / verify_admin_password, 0 nilai hash.

Riwayat (jujur): draf v11 pertama (staging ...-v11-try-exact.jsonl)
TIDAK digabung — baris tool-call-nya mencampur prosa dengan JSON, dan
Jaccard menurut ukur bokone 0,317 internal / 0,357 vs dasar (di atas
0,3). File draf itu juga tidak lolos pemeriksaan keamanan, jadi tidak
dipakai apa adanya. Batch dibangun ulang bersih (v2) dari diagnosis tes
v10. Pelajaran: bokone sempat salah menandai kunci "input" di draf v1
sebagai cacat — padahal format dataset WAJIB {instruction, input,
output} (notebook Colab assert itu). Draf v2 awalnya justru menghilangkan
"input"; ketahuan saat cek gabung, diperbaiki (input:"" di 12 baris)
sebelum merge. Cek kunci harus ke assert notebook, bukan ke asumsi.

Perbaikan kode terkait (commit 2f011ba0, sudah di-push terpisah):
<|fim_suffix|> (id 151661) dan <|fim_middle|> (id 151660) sama seperti
<|fim_pad|> — TIDAK special di tokenizer Qwen2.5-Coder, jadi bocor ke
output mentah v10. local_brain.py _generate + run_kumar.py ask() kini
memasukkan keduanya ke eos dan memotong manual (pola sama seperti
perbaikan fim_pad).

## Aturan ke depan

- Setiap lab pagi, bounty, perbaikan bug, dan uji adapter yang
  selesai → diubah jadi contoh dalam sehari.
- Satu kejadian nyata = satu atau beberapa contoh; jangan mengarang
  kejadian yang tidak terjadi.
- Penalaran dulu, baru jawaban/tool-call. Fakta live (peringkat,
  harga, tanggal) hanya dari sumber terverifikasi.
- Target: ~1000 contoh. Kecepatan jujur dari pekerjaan nyata:
  ~15–25 contoh/hari → sekitar 5–6 minggu.
