# Pelajaran

Pelajaran dari kesalahan agen. Dibaca sebelum setiap tugas baru.
Jangan ulangi kesalahan yang sudah tercatat di sini.

- Kesalahan: Setelah cek header dasar, langsung berhenti dan menyimpulkan. | Perbaikan: Setelah cek header, selalu lanjut uji form pencarian dan laporan, dan sarankan jalankan tools/sql_scan.py. | Konteks: run pertama ke verifydeal.site, 2026-11-11
- Kesalahan: Menyimpulkan "aman" hanya karena tidak ada sinyal kuat. | Perbaikan: "Tidak ada sinyal" artinya belum ditemukan, bukan aman. Tulis itu dengan jelas dan lanjutkan audit kode. | Konteks: sql_scan
- Kesalahan: Mengulang cara yang sama saat tool gagal (timeout / 404). | Perbaikan: Coba satu cara lain, catat apa yang gagal dan kenapa, jangan ulang cara yang sama persis.
- Kesalahan: Menjalankan scan tanpa memastikan itu website sendiri. | Perbaikan: Selalu pastikan target adalah website sendiri / yang ada izin tertulis, dan hanya pakai payload non-destruktif.
- Kesalahan: Menjawab tanpa membaca pelajaran lama. | Perbaikan: Baca file ini dulu sebelum tugas baru.
- Kesalahan: Perintah "lanjut scan SQL-nya" dijawab dengan search_web (hasilnya tutorial SQL umum dari Medium/Scribd), bukan menjalankan tools/sql_scan.py ke URL terakhir. | Perbaikan: Kalau ada kata "scan SQL", jalankan scan_sql ke URL terakhir yang dicek (param default "q", atau param yang user sebut). Kalau belum ada URL, tanya URL-nya dulu — jangan cari tutorial di web. | Konteks: chat v2, 2026-11-11, "lanjut scan SQL-nya" setelah cek verifydeal.site
