"""tools/admin_password.py — verifikasi password admin verifydeal.site.

Kenapa tool ini ada: titik masuk password verifydeal.site BUKAN kolom
form, melainkan dialog JS prompt() yang mengirim password mentah sebagai
header x-admin-password ke endpoint tulis (/api/data, /api/upload,
/api/vote). Tidak ada endpoint baca yang memverifikasi password — jadi
cara menguji "apakah password admin ini benar" adalah dengan mengirim
satu request tulis yang SUDAH PASTI GAGAL di tahap validasi body.

Mekanisme aman yang dipakai tool ini (diprobing dari lab 2026-11-16,
tidak ada data yang berubah):
- Server memeriksa password DULU, sebelum validasi body. DELETE
  /api/data/-1 tanpa password -> 401; dengan password salah -> 401.
  POST /api/data body {} tanpa password -> 401; dengan password salah
  -> 401.
- Password BENAR + body {} -> lolos auth, lalu GAGAL validasi body
  (422) karena {} tidak punya field wajib — TIDAK ADA data yang
  ditulis. Jadi: 401 = password salah, 422/400 = password DITERIMA
  dan tidak ada yang berubah.
- Body request HARUS {} (tidak valid, tidak bisa tersimpan). Jangan
  pernah mengirim body yang valid ke endpoint tulis dari tool ini.

Aturan keras:
- Password dibaca HANYA dari environment (.env di Codespace,
  nama var VERIFYDEAL_ADMIN_PASSWORD). Lion yang mengetik password
  itu sendiri ke .env-nya.
- Password TIDAK PERNAH lewat chat, repo, atau dataset. Tool ini
  TIDAK PERNAH mencetak atau me-log nilai password — pesan error pun
  tidak menyebut nilainya.
- Tool ini khusus verifydeal.site (situs Lion sendiri). Jangan pakai
  password ini untuk situs lain, dan jangan memverifikasi password
  situs lain dengan tool ini.
"""

import os
from urllib.parse import urlparse

import requests

_ENV_VAR = "VERIFYDEAL_ADMIN_PASSWORD"
_HEADERS = {"User-Agent": "lion-cyber-agent/0.1 (audit website sendiri)"}
_DEFAULT_URL = "https://www.verifydeal.site/"


def verify_admin_password(url=_DEFAULT_URL, timeout=15):
    """Verifikasi password admin dari .env ke satu situs (default verifydeal.site).

    POST {url}/api/data dengan body {} + header x-admin-password.
    Kembalikan dict: url, accepted, status, message, changed (selalu False).
    - 401 -> accepted False: "Password salah / tidak diterima server."
    - 422/400 -> accepted True: "Password diterima. Tidak ada data yang berubah."
    - status lain -> accepted False + status jujur.
    Kalau VERIFYDEAL_ADMIN_PASSWORD tidak ada di environment: raise
    ValueError yang jelas (tambahkan ke .env, jangan tulis di chat).
    """
    password = os.environ.get(_ENV_VAR)
    if not password:
        raise ValueError(
            "VERIFYDEAL_ADMIN_PASSWORD belum diatur. Tambahkan "
            "VERIFYDEAL_ADMIN_PASSWORD ke .env di Codespace (Lion yang "
            "mengetiknya sendiri), jangan tulis password di chat atau di repo."
        )
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError(f"URL tidak valid: {url}")
    endpoint = url.rstrip("/") + "/api/data"
    try:
        r = requests.post(
            endpoint,
            json={},
            headers={**_HEADERS, "x-admin-password": password},
            timeout=timeout,
        )
    except requests.RequestException as e:  # noqa: BLE001 - sampaikan apa adanya
        raise ValueError(f"Tidak bisa menghubungi {url}: {e}")
    if r.status_code == 401:
        return {
            "url": url,
            "accepted": False,
            "status": 401,
            "message": "Password salah / tidak diterima server.",
            "changed": False,
        }
    if r.status_code in (400, 422):
        return {
            "url": url,
            "accepted": True,
            "status": r.status_code,
            "message": "Password diterima. Tidak ada data yang berubah.",
            "changed": False,
        }
    return {
        "url": url,
        "accepted": False,
        "status": r.status_code,
        "message": (
            f"Server menjawab status {r.status_code} — tidak bisa memastikan "
            "password diterima atau tidak."
        ),
        "changed": False,
    }
