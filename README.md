# lion-cyber-agent

Agen AI kecil untuk coding dan keamanan siber — dibuat Lion bersama bokone.

Tujuan: menulis kode yang aman, lalu menemukan celah di **website sendiri** untuk diperbaiki (defensive security).

## Yang bisa dilakukan agen ini

1. **Menulis kode aman** — pakai prepared statement, hashing password, validasi input.
2. **Memeriksa website lewat internet** — cari di web, buka URL, baca isi halaman, cek dasar keamanan (HTTPS, header).
3. **Menulis tool-nya sendiri** — kalau belum punya tool untuk suatu pengecekan, agen menulis tool Python-nya, menjalankannya di sandbox, membaca hasilnya, lalu memperbaiki tool itu.

Contoh: belum paham cara scan SQL injection → agen menulis `tools/sql_scan.py`, menjalankannya ke website sendiri, lalu melaporkan hasilnya.

## Struktur

```
agent/          # agen + tools internet
  agent.py      # loop: pikir -> pilih tool -> jalankan -> simpulkan
  tools.py      # search_web, fetch_url, check_site_basic
  main.py       # CLI: python -m agent.main "cek website saya ..."
tools/
  sql_scan.py   # contoh tool scan SQL injection (aman, non-destruktif)
dataset/
  dataset.jsonl # contoh dataset coding + keamanan siber (OWASP Top 10)
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
python -m agent.main "cek https://website-kamu-sendiri.example"
python tools/sql_scan.py --url "https://website-kamu-sendiri.example/login" --param username
```

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

Lihat `dataset/dataset.jsonl` untuk 20 contoh pertama: SQL injection, XSS, CSRF, auth, dan secure coding.
