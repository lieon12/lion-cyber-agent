# Skill Kumar (v4)

Kumar adalah nama agen ini. v4 menambahkan tiga skill baru di atas
skill coding + keamanan siber yang sudah ada: **make.fun** (connect
dan bounty), **GitHub** (cari, baca, dan vetting tool), dan
**evaluasi diri** (nilai kemampuan sendiri dari kenyataan, bukan
perkiraan).

Skill ini lahir dari kerja nyata 2026-11-14: akun @qjack terhubung,
payout di-pin ke wallet Lion, bounty food-picture-01 dipilih, entry
"Honey-glazed crispy pork belly" dibuat dan ter-submit (submission
01a1d76e-f7cb-7374-9ba8-626651d9752e). Semua pelajaran dari kerja itu
ada di `agent/lessons.md` (pelajaran 7–12) dan
`dataset/mistake_lessons.jsonl`.

## 1. make.fun — connect dan bounty (read-only)

Tool: `tools/makefun.py`. API key dibaca dari `MAKEFUN_API_KEY`
di `.env`, tidak pernah ditulis di kode atau di-commit.

| Tool | Fungsi | Endpoint |
| --- | --- | --- |
| `list_open_competitions()` | Daftar bounty yang sedang buka | GET /api/competitions?status=open |
| `competition_status(slug)` | Status satu kompetisi | GET /api/competitions/\<slug\> |
| `my_entry_status(submission_id)` | Status satu entry milik akun | GET /api/submissions/\<id\>/status |

Perintah chat yang dikenali planner (`agent/agent.py`):
"cek bounty make.fun", "kompetisi yang buka", "cek status kompetisi
food-picture-01", "cek status entry 01a1d76e-...".

Yang TIDAK ada di sini, sengaja: **submit dan claim**. Mengirim entry
berarti uang/hadiah, jadi itu langkah yang diawasi — Lion harus
menyetujui setiap submit, dan submit dilakukan lewat kit CLI
(`node cli/makefun.mjs submit`) dengan transcript bundle, bukan
dari tool ini.

Pelajaran penting dari 2026-11-14 (lihat `agent/lessons.md`):
- Halaman kompetisi ada di `https://make.fun/bounty/<slug>` —
  `/c/<slug>` adalah 404.
- Halaman `make.fun/delegate` hanya menandatangani pesan yang
  diawali `make.fun delegation v1;`. Pesan konfirmasi pin payout
  (`make.fun account change v1; ...`) harus di-sign lewat signer
  umum (misal `window.solana.signMessage`).
- Step-up challenge hanya berlaku **5 menit** — buat yang baru
  tepat sebelum Lion sign.
- Kit CLI butuh file credentials format `agent-fun/credentials/v1`
  (bukan format hasil connect HTTP).
- Transcript bundle untuk sesi Muse butuh `--muse-usage` (usage rows
  dari muse.db per agent_id).

## 2. GitHub — cari, baca, dan vetting tool

Tool: `tools/github_tools.py`. API GitHub publik tidak butuh auth
(60 request/jam); kalau `GITHUB_TOKEN` diisi di `.env`, batasnya
naik jadi 5000/jam.

| Tool | Fungsi |
| --- | --- |
| `search_github_tools(query, limit=5)` | Cari repo tool publik, diurutkan berdasarkan bintang |
| `read_repo_file(owner, repo, path)` | Baca satu file dari repo publik (contents API) |
| `vet_tool(repo_full_name)` | Vetting repo: README, lisensi, bintang, arsip, pola berbahaya |

`vet_tool` hanya membaca — tidak pernah clone, download-dan-jalankan,
atau mengeksekusi kode asing. Verdict-nya:
- `layak ditinjau lanjut` — tidak ada pola berbahaya terdeteksi
- `butuh tinjauan manual` — ada temuan / tanpa lisensi / tanpa README
- `jangan pakai` — repo diarsipkan

Verdict BUKAN izin pakai. **Adopsi tool yang lolos vetting adalah
langkah terpisah yang butuh persetujuan Lion.** Menjalankan kode
asing tanpa vetting bisa mencuri key atau merusak mesin.

Perintah chat yang dikenali planner: "cari tool scanner XSS di
github", "vetting repo OWASP/juice-shop", "baca README.md di
OWASP/juice-shop".

## 3. Evaluasi diri

Tool: `tools/self_eval.py` (`run_self_eval()`). Kumar menjalankan
`check_site_basic` dan `scan_sql` miliknya sendiri ke target yang
diizinkan, lalu membandingkan hasilnya dengan temuan yang SUDAH
diketahui dari lab — jadi nilainya dihitung dari kenyataan.

Target yang diuji (hanya yang diizinkan, payload non-destruktif):
- `https://www.verifydeal.site/` — diharapkan: status 200, HSTS ada,
  CSP / X-Frame-Options / X-Content-Type-Options hilang; scan SQL
  param `q`: baseline 200, tidak ada sinyal kuat.
- `https://demo.owasp-juice.shop/` — diharapkan: status 200, HSTS
  dan CSP hilang.
- `http://testphp.vulnweb.com/` — dari mesin lab tidak bisa
  dijangkau (proxy); kalau tiba-tiba bisa, yang diharapkan status 200.

Hasil: pass/fail per target + skor evaluasi diri (persen dari check
yang lolos di target yang bisa dijangkau), ditulis ke
`reports/self-eval-latest.json`. Target yang tidak bisa dijangkau
dicatat `unreachable` — hasilnya tidak pernah dikarang.

**Skor ini terpisah dari persen Coding/Hacking di
`agent/capabilities.py`** (file itu tidak diubah supaya persen lab
pagi tetap bisa dibandingkan dari hari ke hari).

Perintah chat yang dikenali planner: "evaluasi diri", "nilai dirimu",
"evaluasi dirimu".

## Yang masih butuh persetujuan Lion

- **Submit entry make.fun** — setiap submit, satu per satu.
- **Adopsi tool dari GitHub** — walau sudah lolos vetting.
- **Tool / situs baru** — sama seperti sebelumnya, validator
  (`agent/validator.py`) menolak tool dan domain di luar daftar
  yang diizinkan, apa pun kata modelnya.
