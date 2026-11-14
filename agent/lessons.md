# Pelajaran

Pelajaran dari kesalahan agen. Dibaca sebelum setiap tugas baru.
Jangan ulangi kesalahan yang sudah tercatat di sini.

- Kesalahan: Setelah cek header dasar, langsung berhenti dan menyimpulkan. | Perbaikan: Setelah cek header, selalu lanjut uji form pencarian dan laporan, dan sarankan jalankan tools/sql_scan.py. | Konteks: run pertama ke verifydeal.site, 2026-11-11
- Kesalahan: Menyimpulkan "aman" hanya karena tidak ada sinyal kuat. | Perbaikan: "Tidak ada sinyal" artinya belum ditemukan, bukan aman. Tulis itu dengan jelas dan lanjutkan audit kode. | Konteks: sql_scan
- Kesalahan: Mengulang cara yang sama saat tool gagal (timeout / 404). | Perbaikan: Coba satu cara lain, catat apa yang gagal dan kenapa, jangan ulang cara yang sama persis.
- Kesalahan: Menjalankan scan tanpa memastikan itu website sendiri. | Perbaikan: Selalu pastikan target adalah website sendiri / yang ada izin tertulis, dan hanya pakai payload non-destruktif.
- Kesalahan: Menjawab tanpa membaca pelajaran lama. | Perbaikan: Baca file ini dulu sebelum tugas baru.
- Kesalahan: Perintah "lanjut scan SQL-nya" dijawab dengan search_web (hasilnya tutorial SQL umum dari Medium/Scribd), bukan menjalankan tools/sql_scan.py ke URL terakhir. | Perbaikan: Kalau ada kata "scan SQL", jalankan scan_sql ke URL terakhir yang dicek (param default "q", atau param yang user sebut). Kalau belum ada URL, tanya URL-nya dulu — jangan cari tutorial di web. | Konteks: chat v2, 2026-11-11, "lanjut scan SQL-nya" setelah cek verifydeal.site
- Kesalahan: Mencoba sign pesan konfirmasi pin payout ("make.fun account change v1; ...") di https://make.fun/delegate — tombol Sign tidak jalan walau diklik berkali-kali. | Perbaikan: Halaman delegate hanya menandatangani pesan yang diawali "make.fun delegation v1;". Pesan "account change v1" harus di-sign lewat signer umum (window.solana signMessage). | Konteks: pin payout @qjack, 2026-11-14
- Kesalahan: Memakai step-up challenge yang sudah lewat 5 menit. | Perbaikan: Challenge step-up hanya berlaku 5 menit — buat yang baru tepat sebelum Lion sign, lalu langsung daftarkan dengan header X-Step-Up. | Konteks: pin payout @qjack, 2026-11-14
- Kesalahan: Membuka halaman kompetisi di /c/<slug> dan mendapat 404. | Perbaikan: Halaman kompetisi ada di /bounty/<slug>; /c/<slug>/kit hanya untuk unduh kit. | Konteks: food-picture-01, 2026-11-14
- Kesalahan: Menjalankan kit CLI makefun dengan file credentials format lama (hasil connect HTTP) — CLI menolak karena bukan format agent-fun/credentials/v1. | Perbaikan: Migrasikan ~/.makefun/credentials ke format v1 (backup dulu file lamanya). | Konteks: submit food-picture-01, 2026-11-14
- Kesalahan: Membuat transcript bundle tanpa --muse-usage — entry sesi Muse tanpa usage rows ditolak. | Perbaikan: Ambil usage rows dari muse.db per agent_id (dari baris pertama file sesi), tulis ke JSONL, lalu bundle dengan --muse-usage. | Konteks: bundle food-picture-01, 2026-11-14
- Kesalahan: Menjalankan kode dari repo GitHub yang baru ditemukan tanpa memeriksa. | Perbaikan: Vetting dulu (README, lisensi, pola berbahaya), adopsi hanya dengan persetujuan Lion. | Konteks: skill GitHub Kumar, 2026-11-14
