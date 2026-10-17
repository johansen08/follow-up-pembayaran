"""Login toko lewat jendela Chrome: user login manual (termasuk captcha/OTP), lalu cookies diambil otomatis.

Alur `mulai_login(toko)`:
  1. Buka Chrome (profil toko: data/stores/<toko>/chrome-profile) ke TikTok Seller Center.
  2. Tunggu sampai cookie autentikasi (SELLER_TOKEN & sessionid) muncul = user selesai login.
  3. Validasi akun: ambil daftar pesanan, cocokkan seller_id dengan folder toko (cegah cookies salah toko).
  4. Simpan cookies ke data/stores/<toko>/cookies.json, tutup Chrome. UI otomatis menandai toko "Siap".
Cookies lama TIDAK ditimpa bila validasi gagal.
"""

from __future__ import annotations

import socket
import threading
import time
from typing import Callable

from DrissionPage import Chromium

from . import runner
from .browser import opsi_browser
from .config import BASE_URL, LOCAL_PORT
from .orders import ambil_pesanan_belum_bayar
from .stores import Toko, periksa_identitas
from .util import tulis_json

BATAS_MENIT = 10
COOKIE_AUTH = {"SELLER_TOKEN", "sessionid"}
_KUNCI_COOKIE = ("name", "value", "domain", "path", "expires", "httpOnly", "secure", "sameSite")


class LoginGagal(Exception):
    pass


def _sudah_login(tab) -> bool:
    try:
        return COOKIE_AUTH <= {c["name"] for c in tab.cookies(all_domains=True, all_info=True)}
    except Exception:  # halaman sedang berpindah
        return False


def ekspor_cookies(tab) -> list[dict]:
    """Cookies domain tokopedia.com dalam format cookies.json yang dibaca stores.baca_cookies."""
    hasil = []
    for c in tab.cookies(all_domains=True, all_info=True):
        if not str(c.get("domain", "")).lstrip(".").endswith("tokopedia.com"):
            continue
        baru = {k: c.get(k) for k in _KUNCI_COOKIE}
        baru["expires"] = c.get("expires", -1) if c.get("expires") is not None else -1
        baru["path"] = baru["path"] or "/"
        hasil.append(baru)
    return hasil


def _port_terpakai() -> bool:
    with socket.socket() as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", LOCAL_PORT)) == 0


def _kerja_chrome(toko: Toko, lapor: Callable[[str, str], None], batal: threading.Event) -> str:
    """Return 'berhasil' / 'dibatalkan'; raise LoginGagal/RuntimeError bila gagal."""
    with runner._kunci(toko):  # cegah run bot pada toko yang sama selama login
        co = opsi_browser(toko.profile_dir)
        browser = Chromium(co)
        try:
            tab = browser.latest_tab
            tab.get(BASE_URL)
            lapor("menunggu", "Login di jendela Chrome yang terbuka. Jangan ditutup.")
            batas = time.monotonic() + BATAS_MENIT * 60
            coba_lagi = 0.0
            while True:
                if batal.is_set():
                    return "dibatalkan"
                now = time.monotonic()
                if now > batas:
                    raise LoginGagal(f"Waktu login habis ({BATAS_MENIT} menit).")
                if _sudah_login(tab) and now >= coba_lagi:
                    time.sleep(2)  # biarkan halaman selesai berpindah setelah login
                    lapor("memeriksa", "Memeriksa akun toko…")
                    try:
                        seller_id, _ = ambil_pesanan_belum_bayar(tab)
                    except Exception:  # belum benar-benar masuk (mis. masih pilih toko/OTP): tunggu lagi
                        coba_lagi = time.monotonic() + 10
                        lapor("menunggu", "Login di jendela Chrome yang terbuka. Jangan ditutup.")
                        continue
                    periksa_identitas(toko, seller_id)  # RuntimeError bila akun bukan milik toko ini
                    cookies = ekspor_cookies(tab)
                    if not COOKIE_AUTH <= {c["name"] for c in cookies}:
                        raise LoginGagal("Cookies login tidak lengkap, coba ulang.")
                    tulis_json(toko.cookies_file, cookies)
                    return "berhasil"
                time.sleep(1)
        finally:
            browser.quit()


class LoginManager:
    """Satu login pada satu waktu. `kerja` bisa diganti saat uji."""

    def __init__(self, kerja: Callable = _kerja_chrome, port_terpakai: Callable[[], bool] = _port_terpakai):
        self._kerja, self._port_terpakai = kerja, port_terpakai
        self._lock = threading.Lock()
        self._batal = threading.Event()
        self._state: dict | None = None

    def aktif(self) -> bool:
        with self._lock:
            return bool(self._state and self._state["status"] in ("menunggu", "memeriksa"))

    def snapshot(self) -> dict | None:
        with self._lock:
            return dict(self._state) if self._state else None

    def mulai(self, toko: Toko, run_aktif: bool = False) -> None:
        with self._lock:
            if self._state and self._state["status"] in ("menunggu", "memeriksa"):
                raise RuntimeError(f"Login {self._state['nama']} sedang berlangsung")
            if run_aktif:
                raise RuntimeError("Proses kirim sedang berjalan, tunggu selesai dulu")
            if self._port_terpakai():
                raise RuntimeError("Browser bot lain sedang berjalan (port dipakai), tutup dulu")
            self._batal = threading.Event()
            self._state = {"slug": toko.slug, "nama": toko.nama, "status": "menunggu",
                           "msg": "Membuka Chrome…", "t0": time.time()}
        threading.Thread(target=self._jalan, args=(toko, self._batal), daemon=True).start()

    def batal(self) -> None:
        self._batal.set()

    def _set(self, status: str, msg: str) -> None:
        with self._lock:
            if self._state and self._state["status"] in ("menunggu", "memeriksa"):
                self._state.update(status=status, msg=msg)

    def _jalan(self, toko: Toko, batal: threading.Event) -> None:
        try:
            hasil = self._kerja(toko, self._set, batal)
            if hasil == "berhasil":
                self._akhir("berhasil", "Login berhasil, cookies tersimpan.")
            else:
                self._akhir("dibatalkan", "Login dibatalkan.")
        except BaseException as e:
            self._akhir("gagal", " ".join(str(e).split())[:200] or e.__class__.__name__)

    def _akhir(self, status: str, msg: str) -> None:
        with self._lock:
            self._state.update(status=status, msg=msg)
