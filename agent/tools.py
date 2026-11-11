"""Tools internet untuk agen.

Ini adalah 'tangan' agen: modelnya sendiri tidak bisa internet,
tools inilah yang mengambil data live lalu diberikan ke model
untuk dianalisis.
"""
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse


def fetch_url(url, timeout=15):
    """Ambil isi sebuah URL. Kembalikan judul, teks, dan header penting."""
    headers = {"User-Agent": "lion-cyber-agent/0.1 (audit website sendiri)"}
    r = requests.get(url, headers=headers, timeout=timeout)
    soup = BeautifulSoup(r.text, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    text = " ".join(soup.get_text(" ").split())[:8000]
    return {
        "url": url,
        "status": r.status_code,
        "final_url": r.url,
        "server": r.headers.get("Server", ""),
        "content_type": r.headers.get("Content-Type", ""),
        "title": soup.title.string.strip() if soup.title and soup.title.string else "",
        "text": text,
        "security_headers": {
            k: r.headers.get(k, "")
            for k in [
                "Strict-Transport-Security",
                "Content-Security-Policy",
                "X-Frame-Options",
                "X-Content-Type-Options",
            ]
        },
    }


def search_web(query, limit=5):
    """Cari di internet lewat DuckDuckGo HTML (tanpa API key)."""
    r = requests.get(
        "https://html.duckduckgo.com/html/",
        params={"q": query},
        headers={"User-Agent": "lion-cyber-agent/0.1"},
        timeout=15,
    )
    soup = BeautifulSoup(r.text, "html.parser")
    out = []
    for a in soup.select("a.result__a")[:limit]:
        out.append({"title": a.get_text(" ", strip=True), "url": a.get("href", "")})
    return out


def check_site_basic(url):
    """Cek dasar keamanan website sendiri: HTTPS, header, redirect."""
    parsed = urlparse(url)
    result = fetch_url(url)
    findings = []
    if parsed.scheme != "https":
        findings.append("Tidak memakai HTTPS — semua data bisa disadap.")
    else:
        findings.append("Memakai HTTPS.")
    h = result["security_headers"]
    if not h["Strict-Transport-Security"]:
        findings.append("Tidak ada header Strict-Transport-Security (HSTS).")
    if not h["Content-Security-Policy"]:
        findings.append("Tidak ada header Content-Security-Policy (CSP).")
    if not h["X-Frame-Options"]:
        findings.append("Tidak ada header X-Frame-Options — rentan clickjacking.")
    if not h["X-Content-Type-Options"]:
        findings.append("Tidak ada header X-Content-Type-Options.")
    result["findings"] = findings
    return result
