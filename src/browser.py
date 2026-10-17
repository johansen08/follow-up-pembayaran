"""Pengaturan Chrome yang dipakai bot (kirim pesan) dan login toko, supaya keduanya selalu sama."""

from __future__ import annotations

import os
from pathlib import Path

from DrissionPage import ChromiumOptions

from .config import LOCAL_PORT

# Setara Playwright: launch(channel="chrome", headless=False, args=['--force-device-scale-factor=0.8'])
SKALA_TAMPILAN = "--force-device-scale-factor=0.8"

_LOKASI_CHROME = (
    Path(os.environ.get("PROGRAMFILES", r"C:\Program Files")) / "Google/Chrome/Application/chrome.exe",
    Path(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)")) / "Google/Chrome/Application/chrome.exe",
    Path(os.environ.get("LOCALAPPDATA", "")) / "Google/Chrome/Application/chrome.exe",
)


def lokasi_chrome() -> str | None:
    """Google Chrome terpasang (bukan Chromium), atau None -> biarkan DrissionPage mencari sendiri."""
    return next((str(p) for p in _LOKASI_CHROME if p.is_file()), None)


def opsi_browser(profile_dir: Path) -> ChromiumOptions:
    """Chrome asli, tampak (tidak headless), skala 0.8, profil khusus toko, port lokal bot."""
    co = ChromiumOptions().set_local_port(LOCAL_PORT).set_user_data_path(str(profile_dir))
    if (chrome := lokasi_chrome()):
        co.set_browser_path(chrome)
    co.headless(False)
    co.set_argument(SKALA_TAMPILAN)
    return co
