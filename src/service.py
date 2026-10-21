"""Menjalankan FU untuk beberapa toko di thread latar & menyimpan status yang dibaca UI web."""

from __future__ import annotations

import threading
import time
import traceback
from typing import Callable

from . import notif, runner
from .stores import Toko


class SedangJalan(Exception):
    pass


def pesan_galat(e: BaseException) -> str:
    """Ringkas & ramahkan pesan error untuk ditampilkan di kartu toko."""
    teks = " ".join(str(e).split())
    if "no location or size" in teks:
        return "Kotak chat belum tampil/tidak bisa diklik. Cek chat pesanan itu manual, lalu coba lagi."
    return (teks or e.__class__.__name__)[:200]


class RunManager:
    def __init__(self, jalankan_toko: Callable = runner.jalankan_toko,
                 beri_tahu: Callable[[str, str], None] = notif.peringatan):
        self._jalankan_toko = jalankan_toko  # bisa diganti saat uji
        self._beri_tahu = beri_tahu          # pop-up + suara saat proses terhenti
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._state: dict | None = None

    # ---- dibaca UI ----
    def snapshot(self) -> dict | None:
        with self._lock:
            if self._state is None:
                return None
            s = dict(self._state)
            s["per"] = {k: dict(v) for k, v in s["per"].items()}
            s["cur"] = dict(s["cur"]) if s["cur"] else None
            return s

    def aktif(self) -> bool:
        with self._lock:
            return bool(self._state and self._state["active"])

    # ---- kontrol ----
    def mulai(self, daftar: list[Toko], pesan_untuk: Callable[[Toko], str]) -> None:
        with self._lock:
            if self._state and self._state["active"]:
                raise SedangJalan("Proses lain masih berjalan")
            self._stop = threading.Event()
            self._state = {
                "active": True, "stop": False, "t0": time.time(), "t1": None, "idx": 0, "n": len(daftar), "cur": None,
                "per": {t.slug: {"status": "menunggu", "done": 0, "total": 0, "skip": 0, "msg": "", "warn": False}
                        for t in daftar},
            }
        pesan = {t.slug: pesan_untuk(t) for t in daftar}
        threading.Thread(target=self._kerja, args=(daftar, pesan, self._stop), daemon=True).start()

    def hentikan(self) -> None:
        with self._lock:
            if self._state and self._state["active"]:
                self._state["stop"] = True
        self._stop.set()

    # ---- thread kerja ----
    def _ubah(self, slug: str, **kv) -> None:
        with self._lock:
            self._state["per"][slug].update(kv)

    def _kerja(self, daftar: list[Toko], pesan: dict[str, str], stop: threading.Event) -> None:
        try:
            self._loop(daftar, pesan, stop)
        finally:  # apa pun yang terjadi, run harus ditandai selesai (jangan menggantung di "berjalan")
            with self._lock:
                self._state["active"] = False
                self._state["cur"] = None
                self._state["t1"] = time.time()

    def _loop(self, daftar: list[Toko], pesan: dict[str, str], stop: threading.Event) -> None:
        for i, toko in enumerate(daftar, 1):
            with self._lock:
                self._state["idx"] = i
            if stop.is_set():
                self._ubah(toko.slug, status="berhenti", msg="Dihentikan pengguna")
                continue
            self._ubah(toko.slug, status="jalan")
            try:
                self._jalankan_toko(toko, True, 0, pesan[toko.slug],
                                    hook=lambda ev, s=toko.slug: self._hook(s, ev), stop=stop)
            except BaseException as e:  # satu toko gagal tidak menghentikan toko lain
                print(f"[ERROR] {toko.nama}:\n{traceback.format_exc()}")
                self._ubah(toko.slug, status="berhenti", msg=pesan_galat(e))
                self._beri_tahu(f"Proses terhenti: {toko.nama}", pesan_galat(e))
            with self._lock:
                p = self._state["per"][toko.slug]
                if p["status"] == "jalan":
                    p["status"] = "selesai"
                self._state["cur"] = None

    def _hook(self, slug: str, ev: dict) -> None:
        with self._lock:
            p = self._state["per"][slug]
            t = ev["t"]
            if t == "target":
                p["skip"], p["total"] = ev["skip"], ev["total"]
                if not ev["total"]:
                    p["msg"] = "Tidak ada pesanan baru"
            elif t == "proses":
                self._state["cur"] = {"toko": slug, "no": ev["no"]}
            elif t == "hasil":
                p["done"] += 1
                self._state["cur"] = None
                if ev["status"] == "perlu_dicek":
                    p["warn"] = True
            elif t == "captcha":
                p["msg"] = "Captcha terdeteksi: selesaikan di jendela Chrome" if ev["ada"] else ""
            elif t == "selesai" and ev.get("berhenti"):
                p["status"], p["msg"] = "berhenti", ev["berhenti"]
                if ev["berhenti"] != "Dihentikan pengguna":
                    self._beri_tahu(f"Proses terhenti: {slug}", ev["berhenti"])
