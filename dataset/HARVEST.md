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

## Aturan ke depan

- Setiap lab pagi, bounty, perbaikan bug, dan uji adapter yang
  selesai → diubah jadi contoh dalam sehari.
- Satu kejadian nyata = satu atau beberapa contoh; jangan mengarang
  kejadian yang tidak terjadi.
- Penalaran dulu, baru jawaban/tool-call. Fakta live (peringkat,
  harga, tanggal) hanya dari sumber terverifikasi.
- Target: ~1000 contoh. Kecepatan jujur dari pekerjaan nyata:
  ~15–25 contoh/hari → sekitar 5–6 minggu.
