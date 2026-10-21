"""Log berkas terpusat: semua kejadian dan error bisa dibaca dari data/log/ tanpa copy-paste dari konsol.

  data/log/fu-<tanggal>.log   semua output konsol (print) + log, tiap baris berstempel waktu
  data/log/error.log          hanya WARNING ke atas + traceback lengkap (cek berkas ini dulu)

Berkas harian tua (> HARI_SIMPAN hari) dihapus saat program mulai. Mengaktifkan log tidak pernah
boleh membuat program gagal jalan: bila folder/berkas tidak bisa ditulis, program tetap jalan tanpa log berkas.
"""

from __future__ import annotations

import logging
import sys
import threading
import time
import traceback
from logging.handlers import RotatingFileHandler

from .config import ROOT

LOG_DIR = ROOT / "data" / "log"
HARI_SIMPAN = 14
log = logging.getLogger("fu")
_aktif = False


class _Tee:
    """Salin tulisan konsol ke berkas, tiap baris diberi stempel waktu."""

    def __init__(self, asli, berkas, nama: str):
        self._asli, self._berkas, self._nama = asli, berkas, nama
        self._awal_baris = True
        self._kunci = threading.Lock()

    def write(self, teks):
        try:
            if self._asli:
                self._asli.write(teks)
        except Exception:
            pass
        try:
            with self._kunci:
                for potong in teks.splitlines(keepends=True):
                    if self._awal_baris and potong.strip():
                        self._berkas.write(f"{time.strftime('%H:%M:%S')} {self._nama} ")
                    elif self._awal_baris:
                        pass
                    self._berkas.write(potong)
                    self._awal_baris = potong.endswith("\n")
                self._berkas.flush()
        except Exception:
            pass
        return len(teks)

    def flush(self):
        try:
            if self._asli:
                self._asli.flush()
        except Exception:
            pass

    def __getattr__(self, nama):
        return getattr(self._asli, nama)


def _bersihkan_lama() -> None:
    batas = time.time() - HARI_SIMPAN * 86400
    for f in LOG_DIR.glob("fu-*.log"):
        try:
            if f.stat().st_mtime < batas:
                f.unlink()
        except OSError:
            pass


def aktifkan() -> None:
    """Pasang log berkas + penangkap error tak tertangani (thread utama dan thread latar). Aman dipanggil berulang."""
    global _aktif
    if _aktif:
        return
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        _bersihkan_lama()
        berkas = open(LOG_DIR / f"fu-{time.strftime('%Y-%m-%d')}.log", "a", encoding="utf-8", buffering=1)
        berkas.write(f"\n===== program mulai {time.strftime('%Y-%m-%d %H:%M:%S')} =====\n")

        fmt = logging.Formatter("%(asctime)s %(levelname)s [%(threadName)s] %(message)s", "%H:%M:%S")
        err = RotatingFileHandler(LOG_DIR / "error.log", maxBytes=2_000_000, backupCount=3, encoding="utf-8")
        err.setLevel(logging.WARNING)
        err.setFormatter(logging.Formatter("%(asctime)s %(levelname)s [%(threadName)s] %(message)s"))
        log.addHandler(err)

        log.setLevel(logging.INFO)
        log.propagate = False
        # WARNING+ ke konsol; semua level INFO+ ke fu-*.log; WARNING+ juga ke error.log
        sys.stdout = _Tee(sys.stdout, berkas, "")
        sys.stderr = _Tee(sys.stderr, berkas, "ERR")
        konsol = logging.StreamHandler(sys.__stderr__ or None)
        konsol.setLevel(logging.WARNING)
        konsol.setFormatter(fmt)
        log.addHandler(konsol)
        info = logging.StreamHandler(berkas)
        info.setLevel(logging.INFO)
        info.setFormatter(fmt)
        log.addHandler(info)
    except Exception as e:  # log tidak boleh membuat program gagal jalan
        print(f"[log] log berkas tidak aktif: {e!r}")
        return

    def _tak_tertangani(tipe, nilai, tb):
        if not issubclass(tipe, KeyboardInterrupt):
            log.error("Error tak tertangani", exc_info=(tipe, nilai, tb))

    def _thread_tak_tertangani(args):
        if args.exc_type is not SystemExit:
            log.error("Error tak tertangani di thread %s", args.thread.name if args.thread else "?",
                      exc_info=(args.exc_type, args.exc_value, args.exc_traceback))

    sys.excepthook = _tak_tertangani
    threading.excepthook = _thread_tak_tertangani
    _aktif = True
    log.info("log aktif, folder %s", LOG_DIR)


def galat(konteks: str, e: BaseException | None = None) -> None:
    """Catat error beserta traceback lengkapnya (ke error.log, konsol, dan log harian)."""
    if e is not None:
        log.error("%s: %r\n%s", konteks, e, "".join(traceback.format_exception(type(e), e, e.__traceback__)))
    else:
        log.error("%s\n%s", konteks, traceback.format_exc())
