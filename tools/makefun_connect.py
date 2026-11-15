"""tools/makefun_connect.py — alat connect Kumar ke akun make.fun Lion.

Cara pakai (di Codespace, sekali saja):
    pip install cryptography requests   # kalau belum ada
    python tools/makefun_connect.py

Alur (device-code flow — SAMA seperti yang dipakai bokone untuk
menghubungkan dompet agent ke @qjack pada 2026-11-14):
1. Muat keypair agent Kumar dari ~/.makefun/agent-keypair.json;
   kalau belum ada, buat keypair BARU — dompet agent milik Kumar
   sendiri, BUKAN dompet lab bokone (Ck5W...). Keypair TIDAK PERNAH
   dicetak dan TIDAK PERNAH masuk repo.
2. POST /api/agents/connect -> device_code, user_code, link verifikasi.
3. Lion membuka link itu sambil login sebagai @qjack, memeriksa
   kodenya, lalu menyetujui. Kode berlaku 15 menit.
4. Poll /api/agents/connect/token sampai disetujui.
5. Simpan API key ke ~/.makefun/credentials (mode 600) DAN tulis
   MAKEFUN_API_KEY ke .env repo (gitignored) supaya tools/makefun.py
   bisa memakainya (mis. entry_rank). Key TIDAK PERNAH dicetak.

Catatan penting: key baru ini untuk BACA (peringkat, status entry).
Delegasi payout yang sudah ada menunjuk dompet agent lab bokone —
kalau Kumar nanti mau SUBMIT entry dengan dompet barunya, perlu
delegasi baru untuk dompet itu (Lion yang menandatangani, seperti
dulu). Submit tetap butuh persetujuan Lion setiap kali.
"""

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

ORIGIN = os.environ.get("MAKEFUN_ORIGIN", "https://make.fun")
EXPECTED_HANDLE = "qjack"
AGENT_NAME = "kumar"

KEYPAIR_FILE = Path(
    os.environ.get("MAKEFUN_KEYPAIR_FILE", str(Path.home() / ".makefun" / "agent-keypair.json"))
)
CRED_FILE = Path(
    os.environ.get("MAKEFUN_CREDENTIALS", str(Path.home() / ".makefun" / "credentials"))
)
ENV_FILE = Path(os.environ.get("MAKEFUN_ENV_FILE", ".env"))

_B58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def b58encode(data: bytes) -> str:
    """Encode bytes ke base58 (Solana)."""
    n = int.from_bytes(data, "big")
    out = ""
    while n > 0:
        n, r = divmod(n, 58)
        out = _B58_ALPHABET[r] + out
    pad = 0
    for b in data:
        if b == 0:
            pad += 1
        else:
            break
    return "1" * pad + (out or "")


def load_or_create_keypair(path: Path):
    """Muat keypair Solana (JSON array 64 byte) atau buat baru.

    Mengembalikan (private_key, wallet_address). File baru disimpan
    mode 600. Keypair TIDAK PERNAH dicetak.
    """
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey,
    )
    from cryptography.hazmat.primitives.serialization import (
        Encoding,
        PrivateFormat,
        PublicFormat,
    )

    if path.exists():
        raw = json.loads(path.read_text())
        if len(raw) != 64:
            raise SystemExit(f"Keypair di {path} rusak (bukan 64 byte).")
        seed = bytes(raw[:32])
        priv = Ed25519PrivateKey.from_private_bytes(seed)
        pub = priv.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
        if pub != bytes(raw[32:]):
            raise SystemExit(f"Keypair di {path} tidak konsisten (pubkey tidak cocok).")
    else:
        seed = os.urandom(32)
        priv = Ed25519PrivateKey.from_private_bytes(seed)
        pub = priv.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(list(seed + pub)))
        os.chmod(path, 0o600)
        print(f"Keypair agent BARU dibuat di {path} (mode 600).")
    address = b58encode(pub)
    return priv, address


def sign_message(priv, message: str) -> str:
    """Tandatangani pesan persis apa adanya (UTF-8, Ed25519) -> base58."""
    sig = priv.sign(message.encode("utf-8"))
    return b58encode(sig)


def api_post(path: str, body: dict, timeout: int = 30):
    """POST JSON dengan retry (proxy lab kadang memutus koneksi)."""
    last_err = None
    for attempt in range(1, 5):
        try:
            res = requests.post(
                ORIGIN + path,
                json=body,
                headers={"content-type": "application/json"},
                timeout=timeout,
            )
            try:
                data = res.json()
            except ValueError:
                data = {}
            return res.status_code, data
        except requests.RequestException as e:  # noqa: BLE001 - retry dulu
            last_err = e
            time.sleep(2 * attempt)
    return 0, {"error": "network_error", "detail": str(last_err)}


def set_env_var(env_path: Path, key: str, value: str) -> None:
    """Tulis/replace satu baris KEY=value di .env (mode 600)."""
    lines = []
    if env_path.exists():
        lines = env_path.read_text().splitlines()
    found = False
    out = []
    for line in lines:
        if line.strip().startswith(key + "="):
            out.append(f"{key}={value}")
            found = True
        else:
            out.append(line)
    if not found:
        out.append(f"{key}={value}")
    env_path.write_text("\n".join(out) + "\n")
    os.chmod(env_path, 0o600)


def store_credentials(cred_path: Path, key: str, expires_at, user: dict, wallet: str) -> None:
    """Simpan key format agent-fun/credentials/v1 (mode 600)."""
    record = {
        "format": "agent-fun/credentials/v1",
        "default_origin": ORIGIN,
        "keys": {
            ORIGIN: {
                "key": key,
                "expires_at": expires_at,
                "wallet": wallet,
                "user_id": user.get("id"),
                "handle": user.get("handle"),
                "saved_at": datetime.now(timezone.utc).isoformat(),
                "keypair_file": str(KEYPAIR_FILE),
            }
        },
    }
    cred_path.parent.mkdir(parents=True, exist_ok=True)
    cred_path.write_text(json.dumps(record, indent=2) + "\n")
    os.chmod(cred_path, 0o600)


def main() -> int:
    # Kode + link harus langsung terlihat (bukan tertahan di buffer)
    # karena Lion membacanya sambil script menunggu persetujuan.
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except (AttributeError, ValueError):
        pass
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import (  # noqa: F401
            Ed25519PrivateKey,
        )
    except ImportError:
        print("Butuh pustaka 'cryptography'. Pasang dulu:")
        print("    pip install cryptography")
        return 1

    priv, wallet = load_or_create_keypair(KEYPAIR_FILE)
    print(f"Dompet agent Kumar: {wallet}")

    status, start = api_post("/api/agents/connect", {"walletAddress": wallet, "name": AGENT_NAME})
    if status != 200:
        print(f"Gagal memulai connect (HTTP {status}): {start}")
        return 1
    device_code = start.get("device_code")
    user_code = start.get("user_code")
    link = start.get("verification_uri_complete") or start.get("verification_uri")
    expires_in = start.get("expires_in", 900)
    interval = start.get("interval", 5)
    message = start.get("message")
    if not device_code or not message:
        print(f"Jawaban connect tidak lengkap: {start}")
        return 1

    print()
    print("=== MINTA PERSETUJUAN LION ===")
    print(f"Kode: {user_code}")
    print(f"Buka link ini sambil login sebagai @{EXPECTED_HANDLE}:")
    print(f"    {link}")
    print(f"Kode berlaku {expires_in // 60} menit. Periksa kodenya sama, lalu setujui.")
    print("Menunggu persetujuan... (Ctrl+C untuk batal)")
    print()

    signature = sign_message(priv, message)
    deadline = time.time() + (expires_in - 20)
    wait = interval
    while True:
        status, data = api_post("/api/agents/connect/token", {"device_code": device_code, "signature": signature})
        if status == 200:
            key = data.get("key")
            expires_at = data.get("expires_at")
            user = data.get("user") or {}
            if not key:
                print(f"Jawaban token tidak lengkap: {data}")
                return 1
            store_credentials(CRED_FILE, key, expires_at, user, wallet)
            set_env_var(ENV_FILE, "MAKEFUN_API_KEY", key)
            handle = user.get("handle")
            ok = handle == EXPECTED_HANDLE
            print("=== TERHUBUNG ===")
            print(f"Handle: @{handle} (diharapkan @{EXPECTED_HANDLE}: {'cocok' if ok else 'TIDAK COCOK'})")
            print(f"Key berlaku sampai: {expires_at}")
            print(f"Key tersimpan di: {CRED_FILE} (mode 600)")
            print(f"MAKEFUN_API_KEY ditulis ke: {ENV_FILE} (mode 600, gitignored)")
            print("Key TIDAK PERNAH dicetak di sini.")
            if not ok:
                print("PERINGATAN: handle yang terhubung bukan qjack — jangan pakai key ini sebelum dicek.")
                return 2
            print("Sekarang coba di chat Kumar: berapa peringkat saya di food-picture-01?")
            return 0
        err = data.get("error") if isinstance(data, dict) else None
        if status == 0 or err in ("network_error", "authorization_pending"):
            if time.time() + wait > deadline:
                print("Waktu habis — persetujuan tidak datang sebelum kode kedaluwarsa. Jalankan lagi.")
                return 1
            time.sleep(wait)
            continue
        if err == "slow_down":
            wait = min(wait + 5, 60)
            time.sleep(wait)
            continue
        print(f"Gagal saat menunggu token (HTTP {status}): {data}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
