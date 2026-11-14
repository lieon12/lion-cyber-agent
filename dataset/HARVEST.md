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

## Aturan ke depan

- Setiap lab pagi, bounty, perbaikan bug, dan uji adapter yang
  selesai → diubah jadi contoh dalam sehari.
- Satu kejadian nyata = satu atau beberapa contoh; jangan mengarang
  kejadian yang tidak terjadi.
- Penalaran dulu, baru jawaban/tool-call. Fakta live (peringkat,
  harga, tanggal) hanya dari sumber terverifikasi.
- Target: ~1000 contoh. Kecepatan jujur dari pekerjaan nyata:
  ~15–25 contoh/hari → sekitar 5–6 minggu.
