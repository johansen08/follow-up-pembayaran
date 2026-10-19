"""Menjalankan FU untuk satu toko."""

from __future__ import annotations

import os
import random
import threading
import time
from contextlib import contextmanager
from typing import Callable

from DrissionPage import Chromium

from . import chat
from .browser import opsi_browser
from .captcha import Pemantau
from .config import BASE_URL, JEDA_MAX, JEDA_MIN
from .orders import ambil_pesanan_belum_bayar
from .send_log import LogKirim
from .stores import Toko, baca_cookies, periksa_identitas


@contextmanager
def _kunci(toko: Toko):
    """Satu proses per toko: cegah dua instans jalan bersamaan (bisa kirim ganda)."""
    try:
        os.close(os.open(toko.lock_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
    except FileExistsError:
        raise RuntimeError(f"{toko.lock_file} ada: program lain sedang jalan untuk toko ini. "
                           "Hapus file itu bila yakin tidak ada.")
    try:
        yield
    finally:
        toko.lock_file.unlink(missing_ok=True)


def _buka_browser(toko: Toko) -> Chromium:
    # Profil Chrome terpisah per toko supaya sesi/cookie toko lain tidak tercampur.
    co = opsi_browser(toko.profile_dir)
    browser = Chromium(co)
    tab = browser.latest_tab
    tab.get(BASE_URL)
    tab.set.cookies(baca_cookies(toko))
    return browser


Hook = Callable[[dict], None]


def _emit(hook: Hook | None, **ev) -> None:
    if hook:
        hook(ev)


def _jeda(stop: threading.Event | None) -> None:
    detik = random.uniform(JEDA_MIN, JEDA_MAX)
    if stop:
        stop.wait(detik)  # langsung bangun bila user menekan Hentikan
    else:
        time.sleep(detik)


def jalankan_toko(toko: Toko, kirim: bool, limit: int, pesan: str,
                  hook: Hook | None = None, stop: threading.Event | None = None) -> None:
    """`hook(event)` dipanggil untuk melaporkan progres (dipakai UI web); `stop` menghentikan run
    setelah pesanan yang sedang diproses selesai. Event: target, proses, hasil, selesai."""
    print(f"\n=== {toko.nama} ===")
    if not toko.siap():
        print(f"[lewati] {toko.cookies_file} belum ada")
        _emit(hook, t="selesai", berhenti="Belum login (cookies.json belum ada)")
        return

    with _kunci(toko):
        log = LogKirim(toko)
        browser = _buka_browser(toko)
        pemantau = Pemantau(browser, toko.nama, hook).__enter__()  # beri tahu bila captcha menahan proses
        try:
            seller_id, belum = ambil_pesanan_belum_bayar(browser.latest_tab)
            periksa_identitas(toko, seller_id)

            if kirim:
                _rekonsiliasi(browser, belum, log, pesan, stop)
            target = [o for o in belum if o["order_id"] not in log]
            print(f"[fu] belum bayar: {len(belum)} | sudah di-FU (log): {len(belum) - len(target)} | target: {len(target)}")
            if limit:
                target = target[:limit]
            for o in target:
                print(f" - {o['order_id']}  {o['pembeli']}  {o['total']}")
            if not kirim:
                _dry_run(browser, target, pesan)
                print("[fu] DRY-RUN, tidak ada yang dikirim. Tambah --kirim untuk mengirim.")
                return

            _emit(hook, t="target", belum=len(belum), skip=len(belum) - len([o for o in belum if o["order_id"] not in log]),
                  total=len(target))
            _, berhenti = _kirim_semua(browser, target, log, pesan, hook, stop)
            _emit(hook, t="selesai", berhenti=berhenti)
        finally:
            pemantau.__exit__(None, None, None)
            browser.quit()


_KEPUTUSAN = {
    chat.PERLU_KIRIM: "PERLU KIRIM (pesan belum ada di chat)",
    chat.SUDAH_ADA: "TIDAK PERLU KIRIM (pesan yang sama sudah ada di chat)",
    chat.BELUM_KETIK: "TIDAK BISA DICEK (kotak input chat tidak ditemukan)",
}


def _dry_run(browser, target: list[dict], pesan: str) -> None:
    """Buka chat tiap pesanan dan putuskan perlu dikirim atau tidak. Tidak mengetik & tidak menulis log."""
    ringkas = {}
    for n, o in enumerate(target, 1):
        oid = o["order_id"]
        if not o["chat_link"]:
            hasil, teks = "tanpa_link", "DILEWATI (tidak ada link chat)"
        else:
            hasil = chat.periksa_lewat_ui(browser, o, pesan)
            teks = _KEPUTUSAN[hasil]
        ringkas[hasil] = ringkas.get(hasil, 0) + 1
        print(f"[{n}/{len(target)}] {oid}: {teks}")
        if n < len(target):
            time.sleep(1)
    print(f"[fu] hasil cek: {ringkas}")


def _rekonsiliasi(browser, belum: list[dict], log: LogKirim, pesan: str,
                  stop: threading.Event | None = None) -> int:
    """Pesanan berstatus 'mencoba'/'tidak_pasti' (verifikasi sempat gagal) dicek ulang: bila pesan kita
    ternyata sudah ada di chat, status diubah jadi 'terkirim'. Hanya membaca chat, tidak pernah mengetik."""
    diperbaiki = 0
    for o in belum:
        if stop and stop.is_set():
            break
        oid = o["order_id"]
        if oid not in log or log.status(oid) not in ("mencoba", "tidak_pasti") or not o["chat_link"]:
            continue
        if chat.periksa_lewat_ui(browser, o, pesan) == chat.SUDAH_ADA:
            log.ubah_status(oid, "terkirim")
            diperbaiki += 1
            print(f"[fu] {oid}: pesan ternyata sudah terkirim, status diperbarui")
    return diperbaiki


def _kirim_semua(browser, target: list[dict], log: LogKirim, pesan: str,
                 hook: Hook | None = None, stop: threading.Event | None = None) -> tuple[int, str | None]:
    """Return (jumlah terkirim, alasan berhenti atau None)."""
    terkirim = 0
    berhenti = None
    for n, o in enumerate(target, 1):
        oid = o["order_id"]
        if stop and stop.is_set():
            berhenti = "Dihentikan pengguna"
            break
        if oid in log:  # jaga-jaga duplikat dalam satu run
            continue
        if not o["chat_link"]:
            print(f"[{n}/{len(target)}] {oid} dilewati: tidak ada link chat")
            _emit(hook, t="hasil", no=oid, status="dilewati")
            continue

        # dicatat SEBELUM mengetik: bila program mati di tengah, order ini tetap dianggap sudah dicoba
        def catat_mencoba(oid=oid, o=o):
            log.catat(oid, "mencoba", o["pembeli"])

        _emit(hook, t="proses", no=oid)
        hasil = chat.kirim_lewat_ui(browser, o, pesan, catat_mencoba)
        print(f"[{n}/{len(target)}] {oid} {o['pembeli']}: {hasil.upper()}")

        if hasil == chat.TERKIRIM:
            log.ubah_status(oid, "terkirim")
            terkirim += 1
            _emit(hook, t="hasil", no=oid, status="terkirim")
        elif hasil == chat.SUDAH_ADA:
            log.catat(oid, "sudah_ada_di_chat", o["pembeli"])
            _emit(hook, t="hasil", no=oid, status="dilewati")
            continue  # tidak mengirim apa pun, tak perlu jeda
        elif hasil == chat.TIDAK_PASTI:
            log.ubah_status(oid, "tidak_pasti")
            print("[fu] BERHENTI: pengiriman tidak terverifikasi. Cek chat order ini manual; "
                  "order tetap di log sehingga TIDAK akan dikirim ulang.")
            _emit(hook, t="hasil", no=oid, status="perlu_dicek")
            berhenti = f"Cek chat pesanan {oid} secara manual"
            break
        else:
            _emit(hook, t="hasil", no=oid, status="dilewati")
            if n == 1:  # BELUM_KETIK pada pesan pertama: kemungkinan selector salah
                print("[fu] pesan pertama gagal - berhenti agar selector dicek dulu.")
                berhenti = "Kotak chat tidak ditemukan/tidak bisa diklik, coba lagi atau cek selector"
                break
        _jeda(stop)
    print(f"[fu] selesai, terkirim {terkirim}")
    return terkirim, berhenti
