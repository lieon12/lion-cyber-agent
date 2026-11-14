# Otak Lokal Kumar (v5) — otak hasil latih + badan agen

Sebelumnya ada dua kubu yang terpisah:

- **Otak saja** (di laptop): `training/run_kumar.py` + adapter
  `kumar-lora-trial.zip` — bisa menjawab pertanyaan teks, tapi tidak
  bisa internet dan tidak bisa pakai tool.
- **Badan saja** (di repo ini): `agent/chat.py` + `agent/tools.py` —
  bisa internet dan pakai tool, tapi otaknya masih aturan sederhana
  atau Gemini (punya Google).

Sejak v5 keduanya digabung: `agent/local_brain.py` memuat adapter
LoRA hasil fine-tune (base Qwen2.5-Coder-0.5B + adapter) sebagai
otak agen. Otak memutuskan tool apa yang dipakai, `agent/chat.py`
menjalankannya lewat validator seperti biasa.

## Cara menjalankan di Codespace

1. **Masukkan adapter ke root repo.** Dari laptop: drag-drop folder
   `kumar-lora-trial` (hasil unzip zip dari Colab) ke file explorer
   Codespace. Atau upload zip-nya lalu di terminal Codespace:
   `unzip kumar-lora-trial.zip` (hasilnya folder `kumar-lora-trial`
   berisi `adapter_config.json`). Folder ini TIDAK di-commit ke
   repo — isinya file biner, dan tiap hasil latih ulang berbeda.
2. **Pasang pustaka model:**
   `pip install torch transformers peft accelerate`
   (Codespace gratis tidak ada GPU — jalan di CPU, agak lambat tapi
   bisa. Kalau mau hemat unduhan: `pip install torch --index-url https://download.pytorch.org/whl/cpu`.)
3. **Jalankan chat dengan otak lokal:**
   `python -m agent.chat --brain local`
   Folder adapter lain: `python -m agent.chat --brain local --adapter ./folder-lain`

## Ganti adapter setelah latih ulang

Tidak perlu ubah kode. Ganti saja isi folder `kumar-lora-trial`
dengan hasil latih yang baru, lalu jalankan perintah yang sama.
Model dasar (~1 GB) diunduh otomatis dari Hugging Face saat
pertama kali jalan.

## Fallback — tidak pernah crash

- Adapter tidak ditemukan / pustaka belum terpasang → chat mencetak
  satu baris alasannya, lalu memakai mode rule-based v2.
- Otak lokal memberi keputusan yang tidak valid (tool tidak dikenal,
  argumen kurang, validator menolak, atau menjawab teks padahal
  tugas jelas butuh tool) → chat mencetak satu baris alasannya,
  lalu memakai mode rule-based v2 untuk tugas itu.
- Mode lain tetap ada: `--brain auto` (Gemini kalau ada key, kalau
  tidak rule-based — perilaku lama, default), `--brain rule`,
  `--brain gemini`.

## Jujur soal kemampuan sekarang

Adapter hasil latih percobaan (37 contoh, lalu 53 dengan contoh
tool-calling v5) **belum bisa diandalkan memanggil tool** — ia
akan sering fallback ke rule-based sampai fine-tune berikutnya
yang benar-benar melatih contoh tool-calling itu. Yang sudah
terbukti jalan: memuat adapter, menjawab pertanyaan, dan merangkum
hasil tool. Makin banyak contoh tool-calling di dataset, makin
jarang fallback-nya.
