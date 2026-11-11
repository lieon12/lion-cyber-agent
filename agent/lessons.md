# Pelajaran

Pelajaran dari kesalahan agen. Dibaca sebelum setiap tugas baru.
Jangan ulangi kesalahan yang sudah tercatat di sini.

- Kesalahan: Setelah cek header dasar, langsung berhenti dan menyimpulkan. | Perbaikan: Setelah cek header, selalu lanjut uji form pencarian dan laporan, dan sarankan jalankan tools/sql_scan.py. | Konteks: run pertama ke verifydeal.site, 2026-11-11
- Kesalahan: Menyimpulkan "aman" hanya karena tidak ada sinyal kuat. | Perbaikan: "Tidak ada sinyal" artinya belum ditemukan, bukan aman. Tulis itu dengan jelas dan lanjutkan audit kode. | Konteks: sql_scan
- Kesalahan: Mengulang cara yang sama saat tool gagal (timeout / 404). | Perbaikan: Coba satu cara lain, catat apa yang gagal dan kenapa, jangan ulang cara yang sama persis.
- Kesalahan: Menjalankan scan tanpa memastikan itu website sendiri. | Perbaikan: Selalu pastikan target adalah website sendiri / yang ada izin tertulis, dan hanya pakai payload non-destruktif.
- Kesalahan: Menjawab tanpa membaca pelajaran lama. | Perbaikan: Baca file ini dulu sebelum tugas baru.
