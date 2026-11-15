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

## Aturan ke depan

- Setiap lab pagi, bounty, perbaikan bug, dan uji adapter yang
  selesai → diubah jadi contoh dalam sehari.
- Satu kejadian nyata = satu atau beberapa contoh; jangan mengarang
  kejadian yang tidak terjadi.
- Penalaran dulu, baru jawaban/tool-call. Fakta live (peringkat,
  harga, tanggal) hanya dari sumber terverifikasi.
- Target: ~1000 contoh. Kecepatan jujur dari pekerjaan nyata:
  ~15–25 contoh/hari → sekitar 5–6 minggu.
