"""tools/admin_password.py — MENCOBA password admin verifydeal.site.

Koreksi Lion 2026-11-16: Kumar TIDAK diberi password (bukan lewat
.env, bukan lewat chat). Dia MENCOBA kandidat password sendiri,
berkali-kali, ke verifydeal.site (situs Lion sendiri). Pembelajaran
ada di loop mencoba itu — bukan di menerima password jadi.

Kenapa tool ini ada: titik masuk password verifydeal.site BUKAN kolom
form, melainkan dialog JS prompt() yang mengirim password mentah sebagai
header x-admin-password ke endpoint tulis (/api/data, /api/upload,
/api/vote). Tidak ada endpoint baca yang memverifikasi password — jadi
cara menguji "apakah password ini benar" adalah dengan mengirim satu
request tulis yang SUDAH PASTI GAGAL di tahap validasi body.

Mekanisme aman yang dipakai tool ini (diprobing dari lab 2026-11-16,
tidak ada data yang berubah):
- Server memeriksa password DULU, sebelum validasi body. DELETE
  /api/data/-1 tanpa password -> 401; dengan password salah -> 401.
  POST /api/data body {} tanpa password -> 401; dengan password salah
  -> 401.
- Password BENAR + body {} -> lolos auth, lalu GAGAL validasi body
  (422) karena {} tidak punya field wajib — TIDAK ADA data yang
  ditulis. Jadi: 401 = kandidat ditolak, coba berikutnya; 422/400 =
  kandidat DITERIMA dan tidak ada yang berubah.
- Body request HARUS {} (tidak valid, tidak bisa tersimpan). Jangan
  pernah mengirim body yang valid ke endpoint tulis dari tool ini.

Batas jujur:
- Mencoba hanya berhasil kalau passwordnya lemah/umum (ada di daftar
  kandidat). Kalau password admin kuat, tidak ada yang diterima — itu
  HASIL YANG BAGUS (password tidak lemah), bukan kegagalan. Kalau
  tidak ada yang diterima: LAPORKAN jujur dan BERHENTI, jangan
  menebak selamanya dan jangan mengarang daftar yang lebih besar.
- Maksimal 20 kandidat per panggilan (ditegakkan), jeda ~0,3 detik
  antar percobaan. Ini audit password lemah di situs Lion sendiri
  saja — JANGAN mencoba password di situs lain.
- Kandidat di sini hanya password UMUM yang lemah (pengetahuan
  publik, bukan rahasia): admin, password, 123456, dst.
"""

import time
from urllib.parse import urlparse

import requests

_HEADERS = {"User-Agent": "lion-cyber-agent/0.1 (audit website sendiri)"}
_DEFAULT_URL = "https://www.verifydeal.site/"
_MAX_ATTEMPTS = 20
_DELAY_BETWEEN_ATTEMPTS = 0.3

# Password umum yang lemah — pengetahuan publik (daftar password
# yang paling sering dipakai orang), BUKAN rahasia dan BUKAN password
# Lion. Dipakai sebagai kandidat pertama saat Kumar diminta mencoba
# password admin verifydeal.site.
DEFAULT_COMMON_PASSWORDS = [
    "admin",
    "password",
    "123456",
    "12345678",
    "qwerty",
    "admin123",
    "password123",
    "12345",
    "123456789",
    "verifydeal",
    "adminadmin",
    "letmein",
    "1234567",
    "123123",
    "111111",
    "000000",
    "abc123",
]


def try_admin_password(passwords=None, url=_DEFAULT_URL, timeout=15):
    """Coba daftar kandidat password admin ke satu situs (default verifydeal.site).

    passwords: daftar kandidat string (maks 20; kalau None, pakai
    DEFAULT_COMMON_PASSWORDS). Tiap kandidat dikirim satu per satu:
    POST {url}/api/data dengan body {} + header x-admin-password.
    Kembalikan dict: url, accepted, password (kandidat yang diterima
    atau None), attempts, tried, status, message, changed (selalu False).
    - 401 -> kandidat ditolak, coba berikutnya.
    - 422/400 -> kandidat DITERIMA, berhenti langsung.
    - Tidak ada yang diterima -> accepted False, password None.
    - Status lain -> berhenti, accepted False + status jujur.
    Daftar lebih dari 20 kandidat, daftar kosong, atau kandidat yang
    bukan string tak-kosong -> ValueError yang jelas.
    """
    if passwords is None:
        passwords = list(DEFAULT_COMMON_PASSWORDS)
    if not isinstance(passwords, (list, tuple)):
        raise ValueError("passwords harus berupa daftar kandidat (list).")
    passwords = list(passwords)
    if not passwords:
        raise ValueError("Daftar kandidat password kosong — tidak ada yang bisa dicoba.")
    if len(passwords) > _MAX_ATTEMPTS:
        raise ValueError(
            f"Terlalu banyak kandidat: {len(passwords)} (maksimal {_MAX_ATTEMPTS} "
            "per panggilan). Berhenti setelah 20 percobaan — jangan menebak selamanya."
        )
    for i, p in enumerate(passwords):
        if not isinstance(p, str) or not p:
            raise ValueError(
                f"Kandidat ke-{i + 1} bukan string tak-kosong — semua kandidat "
                "harus berupa teks password."
            )
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError(f"URL tidak valid: {url}")
    endpoint = url.rstrip("/") + "/api/data"
    attempts = 0
    for candidate in passwords:
        attempts += 1
        try:
            r = requests.post(
                endpoint,
                json={},
                headers={**_HEADERS, "x-admin-password": candidate},
                timeout=timeout,
            )
        except requests.RequestException as e:  # noqa: BLE001 - sampaikan apa adanya
            raise ValueError(f"Tidak bisa menghubungi {url}: {e}")
        if r.status_code == 401:
            if attempts < len(passwords):
                time.sleep(_DELAY_BETWEEN_ATTEMPTS)
            continue
        if r.status_code in (400, 422):
            return {
                "url": url,
                "accepted": True,
                "password": candidate,
                "attempts": attempts,
                "tried": attempts,
                "status": r.status_code,
                "message": (
                    f"Password admin diterima: '{candidate}' (setelah {attempts} "
                    "percobaan). Password ini LEMAH — ganti setelah tes."
                ),
                "changed": False,
            }
        return {
            "url": url,
            "accepted": False,
            "password": None,
            "attempts": attempts,
            "tried": attempts,
            "status": r.status_code,
            "message": (
                f"Server menjawab status {r.status_code} — tidak bisa memastikan "
                "password diterima atau tidak."
            ),
            "changed": False,
        }
    return {
        "url": url,
        "accepted": False,
        "password": None,
        "attempts": attempts,
        "tried": attempts,
        "status": 401,
        "message": (
            "Tidak ada yang diterima — password bukan password umum yang lemah."
        ),
        "changed": False,
    }
