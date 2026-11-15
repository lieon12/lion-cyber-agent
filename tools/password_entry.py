"""tools/password_entry.py — cari SEMUA tempat password dimasukkan di sebuah situs.

Pelajaran dari verifydeal.site (2026-11-15): situs itu TIDAK PUNYA
<input type="password"> sama sekali. Titik masuk password-nya adalah
dialog JS prompt() yang menjaga aksi hapus / upload QRIS / tambah-edit
data / vote, dan password mentah dikirim sebagai header
x-admin-password. Tool yang hanya mencari <input type="password">
akan bilang "tidak ditemukan" dan melewatkan semuanya.

Karena itu tool ini mencari SEMUA cara password dimasukkan:
1. <input type="password"> (form, nama field, autocomplete)
2. Tombol/link yang teks terlihatnya menyebut password / kata sandi
3. Di script same-origin (dan script inline): prompt(...password...),
   string type="password", dan header password (x-admin-password,
   Authorization) beserta aksi yang dijaganya
4. Mengikuti maksimal 3 link login/masuk/signin/admin (same-origin)

Read-only: hanya GET. Tidak pernah submit form, tidak pernah
mengirim atau menebak password.
"""

import re
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

_HEADERS = {"User-Agent": "lion-cyber-agent/0.1 (audit website sendiri)"}

# Kata yang menandakan sesuatu berhubungan dengan password.
_PASSWORD_WORDS = ("password", "kata sandi")
# Header yang membawa password ke API.
_HEADER_RE = re.compile(r"['\"](x-[a-z0-9-]*password|authorization)['\"]", re.IGNORECASE)
_METHOD_RE = re.compile(r"method\s*:\s*['\"](DELETE|POST|PUT|PATCH|GET)['\"]", re.IGNORECASE)
_ENDPOINT_RE = re.compile(r"['\"](/api/[a-z0-9_/\-{}.]+)['\"]", re.IGNORECASE)
# prompt("teks") / prompt('teks') / prompt(`teks`) — teks bisa multi-baris.
_PROMPT_RE = re.compile(r"prompt\s*\(\s*([\"'`])(.*?)\1", re.DOTALL)
_TYPE_PASSWORD_RE = re.compile(r"type\s*=\s*['\"]password['\"]", re.IGNORECASE)
_LOGIN_HREF = ("login", "masuk", "signin", "sign-in", "admin")

_MAX_SCRIPTS = 10
_MAX_LOGIN_LINKS = 3
_SCRIPT_TIMEOUT = 10


def _mentions_password(text):
    low = (text or "").lower()
    return any(w in low for w in _PASSWORD_WORDS)


def _fetch(url, timeout=15):
    try:
        r = requests.get(url, headers=_HEADERS, timeout=timeout)
    except requests.RequestException as e:  # noqa: BLE001 - sampaikan apa adanya
        raise ValueError(f"Tidak bisa mengambil {url}: {e}")
    return r


def _scan_inputs(soup, page_url):
    """Semua <input type="password"> di satu halaman."""
    found = []
    for inp in soup.find_all("input"):
        if (inp.get("type") or "").lower() != "password":
            continue
        form = inp.find_parent("form")
        action = ""
        method = ""
        if form is not None:
            action = urljoin(page_url, form.get("action") or "")
            method = (form.get("method") or "GET").upper()
        found.append(
            {
                "page": page_url,
                "form_action": action,
                "form_method": method,
                "field_name": inp.get("name") or "",
                "field_id": inp.get("id") or "",
                "autocomplete": inp.get("autocomplete") or "",
            }
        )
    return found


def _scan_buttons(soup, page_url):
    """Tombol/link yang teks terlihatnya menyebut password."""
    found = []
    for tag in soup.find_all(["button", "a"]):
        text = tag.get_text(" ", strip=True)
        if not _mentions_password(text):
            continue
        form = tag.find_parent("form")
        entry = {
            "page": page_url,
            "tag": tag.name,
            "text": text[:80],
            "href": urljoin(page_url, tag.get("href") or "") if tag.name == "a" else "",
            "form_action": urljoin(page_url, form.get("action") or "")
            if form is not None
            else "",
        }
        found.append(entry)
    return found


def _scan_script_text(text, page_url, script_url):
    """Cari prompt() password, type='password', dan header password
    di satu teks script. Kembalikan (prompts, type_password_count)."""
    prompts = []
    for m in _PROMPT_RE.finditer(text):
        prompt_text = m.group(2).strip()
        if not _mentions_password(prompt_text):
            continue
        # Jendela sesudah prompt(): aksi apa yang dijaga prompt ini?
        window = text[m.end() : m.end() + 600]
        method = _METHOD_RE.search(window)
        endpoint = _ENDPOINT_RE.search(window)
        headers = sorted({h.lower() for h in _HEADER_RE.findall(window)})
        prompts.append(
            {
                "page": page_url,
                "script": script_url,
                "prompt_text": prompt_text[:160],
                "method": method.group(1).upper() if method else "",
                "endpoint": endpoint.group(1) if endpoint else "",
                "headers": headers,
            }
        )
    n_type_password = len(_TYPE_PASSWORD_RE.findall(text))
    return prompts, n_type_password


def _same_origin(url, base_netloc):
    try:
        return urlparse(url).netloc.lower() == base_netloc
    except Exception:
        return False


def _scan_page(soup, page_url, inputs, prompts, buttons):
    inputs.extend(_scan_inputs(soup, page_url))
    buttons.extend(_scan_buttons(soup, page_url))
    scripts = []
    for tag in soup.find_all("script"):
        src = tag.get("src")
        if src:
            scripts.append(urljoin(page_url, src))
        elif tag.string:
            scripts.append(None)  # inline
            p, n = _scan_script_text(tag.string, page_url, page_url)
            prompts.extend(p)
            if n:
                inputs.append(
                    {
                        "page": page_url,
                        "source": "script-inline",
                        "form_action": "",
                        "form_method": "",
                        "field_name": "",
                        "field_id": "",
                        "autocomplete": "",
                        "note": f"string type=\"password\" muncul {n}x di script inline — "
                        "input dibuat lewat JavaScript",
                    }
                )
    return scripts


def find_password_entry(url, timeout=15):
    """Cari tempat memasukkan password di satu URL (read-only, GET saja).

    Kembalikan dict: url, https, password_inputs, password_prompts,
    password_buttons, login_links_checked, summary.
    Kalau tidak ada yang ditemukan, list kosong dan summary bilang
    begitu dengan jujur — tidak pernah mengarang.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError(f"URL tidak valid: {url}")
    r = _fetch(url, timeout=timeout)
    page_url = r.url
    base_netloc = urlparse(page_url).netloc.lower()
    soup = BeautifulSoup(r.text, "html.parser")

    inputs, prompts, buttons = [], [], []
    script_urls = _scan_page(soup, page_url, inputs, prompts, buttons)

    # Script same-origin (maksimal 10), kegagalan satu script tidak
    # menggagalkan semuanya.
    checked_scripts = 0
    for src in script_urls:
        if src is None or checked_scripts >= _MAX_SCRIPTS:
            continue
        if not _same_origin(src, base_netloc):
            continue
        checked_scripts += 1
        try:
            sr = _fetch(src, timeout=_SCRIPT_TIMEOUT)
        except ValueError:
            continue
        p, n = _scan_script_text(sr.text, page_url, src)
        prompts.extend(p)
        if n:
            inputs.append(
                {
                    "page": page_url,
                    "source": "script",
                    "script": src,
                    "form_action": "",
                    "form_method": "",
                    "field_name": "",
                    "field_id": "",
                    "autocomplete": "",
                    "note": f"string type=\"password\" muncul {n}x di {src} — "
                    "input dibuat lewat JavaScript",
                }
            )

    # Ikuti maksimal 3 link login/masuk/signin/admin (same-origin),
    # ulangi pencarian input + tombol di sana.
    login_links_checked = []
    seen = {page_url}
    for a in soup.find_all("a", href=True):
        if len(login_links_checked) >= _MAX_LOGIN_LINKS:
            break
        href = (a.get("href") or "").lower()
        if not any(k in href for k in _LOGIN_HREF):
            continue
        target = urljoin(page_url, a["href"])
        if not _same_origin(target, base_netloc) or target in seen:
            continue
        seen.add(target)
        login_links_checked.append(target)
        try:
            lr = _fetch(target, timeout=timeout)
        except ValueError:
            continue
        lsoup = BeautifulSoup(lr.text, "html.parser")
        inputs.extend(_scan_inputs(lsoup, lr.url))
        buttons.extend(_scan_buttons(lsoup, lr.url))

    n_in = len(inputs)
    n_pr = len(prompts)
    n_bt = len(buttons)
    if n_in == 0 and n_pr == 0 and n_bt == 0:
        summary = (
            f"Tidak ditemukan tempat memasukkan password di {url} — tidak ada "
            "kolom input password, tombol password, atau dialog prompt password."
        )
    else:
        parts = []
        if n_in:
            parts.append(f"{n_in} kolom input password")
        if n_pr:
            parts.append(f"{n_pr} dialog prompt() yang meminta password")
        if n_bt:
            parts.append(f"{n_bt} tombol/link soal password")
        summary = f"Di {url} ditemukan " + ", ".join(parts) + "."
    return {
        "url": url,
        "https": parsed.scheme == "https",
        "password_inputs": inputs,
        "password_prompts": prompts,
        "password_buttons": buttons,
        "login_links_checked": login_links_checked,
        "summary": summary,
    }
