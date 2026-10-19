"""Pemantau captcha latar belakang.

Captcha TikTok Seller tidak bisa dilewati bot: user harus menggesernya sendiri di jendela Chrome.
Pemantau memeriksa semua tab tiap beberapa detik dan HANYA memberi tahu (pop-up + suara + hook).
Ia hanya membaca halaman, tidak pernah mengklik, dan tidak pernah menunggu.

Penanda dialog sama dengan proyek update-promo-tiktok (diverifikasi dari dialog asli); jangan
dilebarkan jadi contains(@class,"captcha") karena terlalu longgar.
"""

from __future__ import annotations

import threading
from typing import Callable

from . import notif

CAPTCHA_SELECTOR = (
    'xpath://div[@id="captcha_container" '
    'or contains(@class,"captcha_verify_container") '
    'or contains(@class,"secsdk-captcha")]'
)
INTERVAL = 5.0  # detik antar pemeriksaan

# timeout=0: pertanyaannya "terlihat SEKARANG?". Tanpa ini DrissionPage menunggu 10 dtk per locator
# saat tidak ada yang cocok (kasus normal) dan perintah CDP thread kerja ikut mengantre.
_PROBE = 0


def _terlihat_di_tab(tab) -> bool:
    try:
        for e in tab.eles(CAPTCHA_SELECTOR, timeout=_PROBE):
            if e.states.is_displayed:
                return True
        for iframe in tab.eles("xpath://iframe", timeout=_PROBE):
            try:
                if any(e.states.is_displayed for e in iframe.eles(CAPTCHA_SELECTOR, timeout=_PROBE)):
                    return True
            except Exception:
                pass
    except Exception:
        pass
    return False


def captcha_terlihat(browser) -> bool:
    """True bila ada captcha tampil di tab mana pun. Kesalahan (browser ditutup, CDP bentrok) = False."""
    try:
        return any(_terlihat_di_tab(t) for t in browser.get_tabs())
    except Exception:
        return False


class Pemantau:
    """Context manager: `with Pemantau(browser, "Nama Toko", hook): ...`"""

    def __init__(self, browser, nama_toko: str, hook: Callable[[dict], None] | None = None,
                 cek: Callable[[object], bool] = captcha_terlihat, interval: float = INTERVAL,
                 beri_tahu: Callable[[str, str], None] = notif.peringatan):
        self._browser, self._nama, self._hook = browser, nama_toko, hook
        self._cek, self._interval, self._beri_tahu = cek, interval, beri_tahu
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def __enter__(self) -> "Pemantau":
        self._thread = threading.Thread(target=self._loop, name="pemantau-captcha", daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *exc) -> None:
        self._stop.set()

    def _loop(self) -> None:
        tampil = False  # satu kali pemberitahuan per kemunculan, bukan tiap 5 detik
        while not self._stop.wait(self._interval):
            try:
                sekarang = self._cek(self._browser)
                if sekarang and not tampil:
                    print(f"\n[!] CAPTCHA terdeteksi di toko {self._nama}. Selesaikan di jendela Chrome.")
                    if self._hook:
                        self._hook({"t": "captcha", "ada": True})
                    self._beri_tahu(
                        "Captcha terdeteksi",
                        f"Toko {self._nama}: proses tertahan. Selesaikan captcha di jendela Chrome. "
                        "Bila proses sudah berhenti, jalankan ulang setelah captcha beres.")
                elif tampil and not sekarang and self._hook:
                    self._hook({"t": "captcha", "ada": False})
                tampil = sekarang
            except Exception:
                pass  # pemantau tidak boleh mematikan run
