# lion-cyber-agent — Kumar

Agen AI kecil untuk coding dan keamanan siber — dibuat Lion bersama bokone.
Nama agen ini: **Kumar**.

Tujuan: menulis kode yang aman, lalu menemukan celah di **website sendiri** untuk diperbaiki (defensive security) — plus, sejak v4, connect ke layanan lain (make.fun), mengambil tool dari GitHub, dan menilai dirinya sendiri.

## Yang bisa dilakukan agen ini

1. **Menulis kode aman** — pakai prepared statement, hashing password, validasi input.
2. **Memeriksa website lewat internet** — cari di web, buka URL, baca isi halaman, cek dasar keamanan (HTTPS, header).
3. **Menulis tool-nya sendiri** — kalau belum punya tool untuk suatu pengecekan, agen menulis tool Python-nya, menjalankannya di sandbox, membaca hasilnya, lalu memperbaiki tool itu.
4. **Connect ke make.fun** — lihat bounty yang buka, cek status kompetisi dan entry sendiri (read-only; submit tetap butuh persetujuan Lion). Lihat `docs/kumar-skills.md`.
5. **Mengambil tool dari GitHub** — cari repo tool, baca kodenya, vetting dulu sebelum dipakai (adopsi tool tetap butuh persetujuan Lion).
6. **Menilai dirinya sendiri** — jalankan tool-nya ke target yang diizinkan, bandingkan dengan temuan yang sudah diketahui, laporkan skor evaluasi diri.

Contoh: belum paham cara scan SQL injection → agen menulis `tools/sql_scan.py`, menjalankannya ke website sendiri, lalu melaporkan hasilnya.

## Struktur

```
agent/          # agen + tools internet
  agent.py      # loop: pikir -> pilih tool -> jalankan -> simpulkan
  tools.py      # search_web, fetch_url, check_site_basic, scan_sql + wrapper skill Kumar
  chat.py       # CHAT v3: ngobrol seperti AI biasa (python -m agent.chat)
  brain.py      # Otak Gemini v3 (REST API, tanpa SDK tambahan)
  validator.py  # Validator: kode yang menegakkan aturan Lion
  system_prompt.md # Instruksi ketat untuk model
  memory.py     # pelajaran + riwayat chat
  lessons.md    # pelajaran dari kesalahan, dibaca sebelum tugas baru (kini 12 pelajaran)
  main.py       # CLI lama, sekali jalan (legacy)
tools/
  sql_scan.py   # contoh tool scan SQL injection (aman, non-destruktif)
  makefun.py    # skill Kumar: API make.fun read-only (list kompetisi, status entry)
  github_tools.py # skill Kumar: cari/baca/vetting tool dari GitHub (tanpa eksekusi)
  self_eval.py  # skill Kumar: evaluasi diri ke target yang diizinkan
docs/
  kumar-skills.md # penjelasan skill Kumar v4 (make.fun, GitHub, evaluasi diri)
dataset/
  dataset.jsonl # contoh dataset coding + keamanan siber (OWASP Top 10)
  mistake_lessons.jsonl # contoh salah -> benar, untuk belajar dari kesalahan
  README.md     # format dataset
training/
  train_lora.py # skeleton fine-tune LoRA untuk model coder kecil
```

## Cara jalan di Codespace

1. Buka repo ini di GitHub → **Code → Codespaces → Create codespace on main**
2. Tunggu devcontainer selesai (Python 3.11 terpasang otomatis)
3. Di terminal Codespace:

```bash
pip install -r requirements.txt
cp .env.example .env   # isi LLM_API_KEY kamu kalau pakai API, atau pakai model lokal
python -m agent.chat
```

## Laboratorium (dijalankan bokone)

Lab ada di `lab/`. Bokone yang menjalankan kodenya di mesinnya sendiri,
menulis laporan ke `reports/YYYY-MM-DD.md`, lalu push ke repo.
Lion tidak perlu menjalankan apa-apa setiap hari.

```bash
python lab/run_lab.py
```

## Otak Gemini v3

Chat v3 memakai Gemini API sebagai otak, kalau `GEMINI_API_KEY` ada
di `.env`. Kalau tidak ada, chat fallback ke mode rule-based v2.

1. Buat API key di Google AI Studio (jangan kirim key ke chat,
   jangan commit `.env` ke repo):
   https://aistudio.google.com/app/apikey
2. Di Codespace:
```bash
cp .env.example .env
# edit .env, isi GEMINI_API_KEY dan GEMINI_MODEL (default gemini-3.8-flash)
python -m agent.chat
```

Yang menjaga agen tetap nurut bukan modelnya, tapi **validator**
(`agent/validator.py`): sebelum tool dijalankan, kode mengecek
apakah tool itu diizinkan, apakah URL-nya ada di `ALLOWED_DOMAINS`
(website sendiri), dan apakah payload-nya aman. Kalau ditolak,
tool tidak dijalankan, apa pun kata modelnya.

Di dalam chat, ketik seperti ngobrol biasa:
```
Kamu: cek https://website-kamu-sendiri.example
Kamu: lanjut scan SQL-nya
Kamu: itu salah, seharusnya lanjut ke form laporan
Kamu: /pelajaran
Kamu: exit
```

Sejak v2.1, `lanjut scan SQL-nya` benar-benar menjalankan
`tools/sql_scan.py` ke website yang terakhir dicek (bukan lagi
mencari tutorial SQL di web). Param default-nya `q` (form pencarian);
kalau form target pakai nama lain, sebutkan: `scan SQL https://... param username`.
Kalau belum ada website yang dicek, agen akan menanyakan URL-nya dulu.

Perintah lama `python -m agent.main "prompt"` masih ada, tapi tidak
disarankan — chat v2 yang dipakai sehari-hari.

Tool scan langsung tetap bisa:
```bash
python tools/sql_scan.py --url "https://website-kamu-sendiri.example/login" --param username
```

## Belajar dari kesalahan

Agen membaca `agent/lessons.md` sebelum setiap tugas. Kalau dia
salah, atau kamu koreksi dia dengan menulis "itu salah", dia akan
bertanya apa perbaikannya, lalu menyimpan pelajaran itu ke
`agent/lessons.md` supaya tidak diulangi.

Pelajaran pertama: setelah cek header dasar, jangan berhenti —
lanjut uji form pencarian dan laporan, dan sarankan `tools/sql_scan.py`.

Website `verifydeal.site` adalah situs pengujian — jangan diperbaiki
dulu, biarkan agen ini yang menemukan dan memperbaikinya nanti.


## Keamanan — baca dulu

- **Hanya scan website milikmu sendiri**, atau yang kamu punya izin tertulis untuk diuji.
- Tool di repo ini memakai payload non-destruktif saja (tidak ada `DROP`, `DELETE`, `UPDATE`).
- Jangan jalankan ke website orang lain, ke website produksi yang live tanpa izin, atau dengan data asli.
- Setelah dana / pengujian selesai, jangan pakai ulang kredensial atau screenshot yang sudah dibagikan.

## Model

Repo ini tidak berisi model besar. Model dasar yang disarankan untuk fine-tune:

- `Qwen/Qwen2.5-Coder-1.5B` (kecil, cepat) atau `Qwen2.5-Coder-7B`
- `meta-llama/Llama-3.1-8B`

Lihat `training/train_lora.py` untuk langkah LoRA. Latih di Codespace dengan GPU atau di Google Colab, bukan di mesin kecil tanpa GPU.

## Dataset

Format JSONL, satu contoh per baris:

```json
{"instruction": "...", "input": "...", "output": "..."}
```

Lihat `dataset/dataset.jsonl` untuk 29 contoh pertama: SQL injection, XSS, CSRF, auth, dan secure coding — plus 9 contoh skill Kumar (make.fun, GitHub, evaluasi diri).
