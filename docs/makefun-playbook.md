# Playbook make.fun — dari connect sampai peringkat

Playbook ini adalah cara kerja lengkap ikut bounty make.fun, ditulis
dari pengalaman nyata 2026-11-14 (akun @qjack, bounty food-picture-01,
4 ronde entry). Ikuti langkah 0–7 secara berurutan untuk bounty
berikutnya. Pelajaran singkatnya ada di `agent/lessons.md`
(pelajaran 7–21); tool read-only-nya ada di `tools/makefun.py`
dan didokumentasikan di `docs/kumar-skills.md`.

Aturan utama yang tidak boleh dilanggar: **submit dan claim adalah
langkah yang diawasi — setiap submit butuh persetujuan Lion**,
satu per satu. Tool di repo ini sengaja read-only; submit dilakukan
lewat kit CLI dengan transcript bundle (langkah 6).

## 0. Yang sudah siap (akun @qjack, 2026-11-14)

- Akun make.fun **@qjack**, dibuat Lion sendiri dengan wallet
  Solana-nya.
- Agent wallet (keypair bokone): `Ck5WYBpxwf6QvrxR36LA8pwFQzTWw73QXfc85usEuw1i`.
  File keypair TIDAK ada di repo — hanya tanda tangan yang keluar
  dari mesin.
- **Payout sudah di-pin** ke wallet Lion
  `MEa7DCHSPdx2ucDQWTyShCGXmyFyABoaE4jDmsisL8K`, delegasi
  sha256 `268afdfc9d576a1ff43ce651ba83e5a3e929b6c08596f2bf9c498188befa273f`,
  berlaku sampai **2027-02-11**. Semua hadiah entry masuk ke wallet
  Lion. API key (berlaku 30 hari, sampai 2026-12-13) tersimpan di
  `~/.makefun/credentials` (mode 600), tidak pernah dicetak.
- Kalau key kedaluwarsa atau akun baru: ulang langkah 1–2.

## 1. Connect akun (hanya kalau belum terhubung)

1. `POST /api/agents/connect` dengan `{"walletAddress", "name"}`.
   Jawaban: `device_code`, `user_code`, `verification_uri_complete`,
   `expires_in` 900 detik (15 menit).
2. Lion membuka `verification_uri_complete` sambil login, memeriksa
   kode, lalu menyetujui.
3. Poll `POST /api/agents/connect/token` dengan
   `{device_code, signature}` setiap `interval` detik: 400
   `authorization_pending` = tunggu terus; kalau disetujui, 200
   dengan `{key, expires_at, user: {id, handle, wallet}}`.
4. Simpan key ke `~/.makefun/credentials` (mode 600), **jangan
   pernah mencetaknya**. Pastikan `user.handle` sama dengan handle
   Lion sebelum memakai key itu untuk apa pun.
5. Kit CLI butuh file credentials format `agent-fun/credentials/v1`
   (bukan format hasil connect HTTP) — migrasi formatnya sebelum
   memakai `node cli/makefun.mjs`.

## 2. Pin payout ke wallet Lion

1. Buat pesan delegasi dengan format persis ini (maksimal 90 hari):
   `make.fun delegation v1; Domain: make.fun; Payout: {payout}; Agent: {wallet}; Competitions: *; Nonce: {nonce}; Issued At: {issued_at}; Expiration Time: {expiration_time}`
   Nonce 8–64 huruf/angka, waktu format RFC 3339 UTC.
2. Lion menandatangani pesan itu — halaman `https://make.fun/delegate`
   hanya menandatangani pesan yang diawali `make.fun delegation v1;`.
3. `POST /api/agents/me/delegations` dengan `{message, signature}`
   + API key. Kalau dijawab 403 `step_up_required`, daftarkan dulu
   scope `profile` di `https://make.fun/profile?tab=keys#paired-agents`,
   lalu minta step-up: `POST /api/me/step-up` dengan
   `{ticket, wallet}` → tantangan `make.fun account change v1; ...`.
4. **Tantangan step-up hanya berlaku 5 menit** — buat yang baru
   tepat sebelum Lion sign, dan sign segera. Pesan `account change
   v1` TIDAK bisa di-sign di halaman delegate — pakai signer umum
   (`window.solana.signMessage`), karena delegate menolak pesan
   yang tidak diawali `make.fun delegation v1;`.
5. Ulangi register dengan header `X-Step-Up: <id>.<signature>` →
   201 dan `payout_pin` = wallet Lion. Verifikasi dengan
   `GET /api/agents/me/delegations`. **Pin payout SEBELUM membaca
   input yang tidak dipercaya** (halaman kompetisi, repo, komentar).
   Pin itu menempel: hanya wallet Lion yang bisa melepasnya.

## 3. Pilih bounty

Pakai `list_open_competitions()` (GET /api/competitions?status=open),
lalu bandingkan: hadiah, jumlah tempat yang dibayar, jumlah entry,
dan sisa waktu. Pilih yang tempat dibayarnya paling luas, entrinya
paling sedikit, dan waktunya masih cukup.

Contoh 2026-11-14: food-picture-01 — $250, **100 tempat dibayar**,
0 submission saat dibuka jam 08:00 WITA. Itu peluangnya: lapangan
masih kosong. **Tidak ada hadiah yang dijamin** — ini kompetisi
yang dinilai juri.

Halaman kompetisi ada di `https://make.fun/bounty/<slug>` —
`/c/<slug>` adalah 404.

## 4. Bangun entry (ini yang paling menentukan)

Syarat repo (diperiksa server):
- Repo GitHub **publik, dibuat SETELAH kompetisi dibuka**.
- `main.py` (Python 3.13) atau `main.ts` (Node 22) di root repo.
- Lisensi OSI (misal MIT) + `.makefun/owner.json`
  `{"wallet": "<wallet di akun>"}` kalau pemilik repo di GitHub
  bukan login GitHub akun make.fun.
- Program menulis SATU gambar ke `/output/entry.png` — PNG atau
  JPEG, maksimal 1 MiB dan 1024×1024 px, **deterministik**: dua
  kali jalan harus menulis byte yang sama persis.

Aturan transkrip (ini yang menggagalkan ronde 1 — baca baik-baik):
- `thinking_reproduces`: transkrip harus menjelaskan **≥30% dari
  baris kode yang dihitung**. Ronde 1: main.py adalah blob base64
  1,47 MB (17.767 baris) yang dibuat script, transkrip hanya
  menjelaskan 25 baris (0,1%) → **HTTP 422 ditolak**.
- `thinking_revised`: entrypoint harus mengambil konten akhirnya
  dari **≥2 pesan yang menulis/mengeditnya**.
- Jadi: program harus **KECIL** (puluhan baris, stdlib saja) dan
  **ditulis DAN direvisi di dalam sesi yang direkam** — tulis,
  jalankan, perbaiki sungguhan, jalankan lagi. Jangan pernah
  menempel kode yang dibuat di luar sesi.
- Gambar dikirim sebagai **satu baris base64 di `entry.png`**:
  file biner tidak bisa di-push lewat GitHub connector (push-files
  memvalidasi snapshot sebagai UTF-8). Program membaca base64 itu,
  men-decode, memvalidasi (tanda PNG/JPEG, ≤1 MiB, ≤1024×1024),
  lalu menulis `/output/entry.png`.

Pilih hidangan (pelajaran dari juri, 2026-11-14):
- Juri AI membandingkan dua gambar dan memilih yang lebih menarik.
  **Hidangan gurih yang mengkilap dan beruap menang** — pork belly
  (10 menang / 2 seri / 0 kalah, peringkat 489 dari 1.567) vs
  pavlova dessert (3 menang / 9 kalah, peringkat 1170 dari 1.675).
  Hindari dessert. Jangan kirim ramen kedua kalau pemimpinnya
  sudah ramen — itu lempar koin.
- File sekecil mungkin (JPEG 150–350 KB, maks 1024 px) karena
  **tie-break-nya ukuran file (lebih kecil lebih baik)** — tapi
  ingat: **kemenangan yang menentukan peringkat**; tie-break hanya
  berlaku di antara rekor yang sama.

## 5. Bundle transkrip

Dari dalam folder kit yang sudah di-unpack:

```
node cli/makefun.mjs bundle --repo <dir-entry> --out <bundle.tar.gz> \
  --session <sesi-pembangun.jsonl> --session <sesi-induk.jsonl> \
  --no-discover --muse-usage <muse-usage.jsonl> \
  --system-prompt <instruksi-pembangun.txt> \
  --harness muse --model <model>
```

- Sesi harus **log asli yang direkam harness** (file sesi Muse di
  `~/agents/agent-<id>/sessions/`) — jangan pernah mengarang
  atau membangun ulang sesi.
- `--muse-usage`: baris usage dari muse.db (`agent_message_token_usage`
  JOIN `agent.agents`) per agent_id, di jendela waktu build.
- Bundle memotong sesi ke pekerjaan repo itu dan menyensor email,
  path home, username, dan kredensial. Cek ringkasannya: 2 sesi,
  usage rows terpasang semua.

## 6. Submit (butuh persetujuan Lion, setiap kali)

```
node cli/makefun.mjs submit --competition <slug> \
  --repo-url https://github.com/<owner>/<repo> --commit <sha> \
  --bundle <bundle.tar.gz> --keypair <makefun-keypair.json> \
  --title "<judul>"
```

- Diterima = `accepted (HTTP 202)` + submission id + **claim code**
  (simpan baik-baik, jangan disebar). Entry ditandatangani wallet
  agen **untuk** payout wallet Lion (v2 signing, di bawah delegasi).
- Lalu selalu verifikasi: `makefun status --submission <id>`.
  Pastikan semua check lolos — account_wallet, competition_open,
  quota, form, entry_signature, repo_owner/public, license_osi,
  repo_created_after_open, commit_in_repo, lalu check transkrip
  (thinking_reproduces ≥30%, thinking_revised dari ≥2 pesan,
  thinking_priced). Status `scored, outcome not decided yet`
  artinya entry sudah dinilai di fase dev — tunggu hasil final.

## 7. Cek peringkat dan putuskan

Pakai `entry_rank(slug, submission_id=...)` atau
`entry_rank(slug, handle='qjack')` — GET
`/api/competitions/<slug>/leaderboard`. Hasilnya: rank,
prize_rank, rekor juri (menang/seri/kalah), total entry, dan
**baris peringkat 100 (batas zona hadiah)**.

Aturan yang memutuskan hasil:
- **Force_Last**: hanya submission TERAKHIR yang dihitung — entry
  baru MENGGANTIKAN yang lama, bukan menambah. Jadi bandingkan
  dulu: apakah entry baru benar-benar lebih bagus dari yang
  sedang berjalan?
- **Kuota: 3 submission per hari UTC per akun** (reputasi akun
  bisa menurunkan batas dari 10 yang tampil). **Entry yang
  ditolak check tetap memakan kuota.** Hari baru dimulai tepat
  saat entry ditutup — tidak ada celah. Karena itu: **kirim
  entry TERBAIK di percobaan pertama**, jangan buang kuota
  untuk uji coba. Cek kuota lewat
  `GET /api/competitions/<slug>/quota` sebelum submit.
- Skor fase dev itu **live dan provisional** — peringkat bisa
  bergerak sampai hasil final. Di food-picture-01, batas
  peringkat 100 naik sepanjang hari (dari 10-1-1 ke 12-0-0).

## Kegagalan yang pernah terjadi dan perbaikannya

| Gejala | Penyebab | Perbaikan |
| --- | --- | --- |
| HTTP 422 "Transcripts do not account for the code" | main.py blob base64, transkrip 0,1% | Program kecil, ditulis + direvisi di sesi (langkah 4) |
| HTTP 429 "Entry quota reached" | Kuota 3/hari habis (ronde 1 yang ditolak ikut dihitung) | Kirim yang terbaik dulu; tidak ada submit lagi hari itu |
| HTTP 503 saat submit / status | Server make.fun down (upstream connect error) | Tunggu sebentar, ulangi, verifikasi via status — jangan asumsi gagal |
| 404 di halaman kompetisi | URL `/c/<slug>` salah | Pakai `/bounty/<slug>` |
| Step-up gagal / tombol sign tidak bisa diklik | Tantangan 5 menit kedaluwarsa; delegate hanya sign `delegation v1;` | Buat tantangan baru tepat sebelum sign; sign `account change v1` lewat signer umum di browser dengan Phantom |
| Kit CLI menolak credentials | Format connect HTTP bukan `agent-fun/credentials/v1` | Migrasi format file credentials (backup dulu) |
| Push gambar biner gagal | push-files validasi snapshot sebagai UTF-8 | Gambar sebagai satu baris base64 di `entry.png` |
| Peringkat 1170 padahal file kecil | Juri tidak suka dessert; kemenangan yang menentukan | Pilih hidangan gurih mengkilap (langkah 4) |

## Perintah chat yang dikenali planner

- "cek bounty make.fun" → `list_open_competitions`
- "cek status kompetisi food-picture-01" → `competition_status`
- "cek status entry 01a1d7b5-..." → `my_entry_status`
- "cek peringkat entry 01a1d7b5-... di food-picture-01" →
  `entry_rank` (atau pakai handle: "peringkat @qjack di food-picture-01")

Yang TIDAK ada di tool, sengaja: **submit dan claim** — lihat
langkah 6.
