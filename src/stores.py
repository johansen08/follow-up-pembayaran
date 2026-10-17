"""Struktur data per toko: data/stores/<nama-toko>/{cookies.json, send_log.json, store.json, chrome-profile/}."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from .config import PESAN_TEMPLATE, STORES_DIR, TOKO
from .util import baca_json, tulis_json


@dataclass(frozen=True)
class Toko:
    nama: str

    @property
    def slug(self) -> str:
        """Nama folder: huruf kecil kebab-case, mis. 'TOKO SAYA' -> 'toko-saya'."""
        return re.sub(r"[\s_]+", "-", self.nama.strip().lower())

    @property
    def dir(self) -> Path:
        return STORES_DIR / self.slug

    @property
    def cookies_file(self) -> Path:
        return self.dir / "cookies.json"

    @property
    def log_file(self) -> Path:
        return self.dir / "send_log.json"

    @property
    def lock_file(self) -> Path:
        return self.dir / "run.lock"

    @property
    def store_file(self) -> Path:
        return self.dir / "store.json"

    @property
    def profile_dir(self) -> Path:
        return self.dir / "chrome-profile"

    @property
    def meta_file(self) -> Path:
        """Pengaturan UI per toko: {"nama": ..., "pesan": template}. Terpisah dari store.json (seller_id)."""
        return self.dir / "meta.json"

    def siap(self) -> bool:
        return self.cookies_file.exists()

    def pesan(self) -> str:
        return baca_json(self.meta_file, {}).get("pesan") or PESAN_TEMPLATE

    def simpan_pesan(self, teks: str) -> None:
        meta = baca_json(self.meta_file, {})
        meta.update({"nama": self.nama, "pesan": teks})
        tulis_json(self.meta_file, meta)


def semua_toko() -> list[Toko]:
    """Toko bawaan (config.TOKO) + toko yang ditambahkan lewat UI (folder dengan meta.json)."""
    daftar = [Toko(n) for n in TOKO]
    ada = {t.slug for t in daftar}
    if STORES_DIR.exists():
        for d in sorted(STORES_DIR.iterdir()):
            nama = baca_json(d / "meta.json", {}).get("nama") if d.is_dir() else None
            if isinstance(nama, str) and Toko(nama).slug == d.name and d.name not in ada:
                daftar.append(Toko(nama))
    return daftar


_POLA_NAMA = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 ._-]{1,39}$")


def tambah_toko(nama: str) -> Toko:
    nama = " ".join(str(nama).split()).upper()
    if not _POLA_NAMA.match(nama):
        raise ValueError("Nama toko 2-40 karakter (huruf, angka, spasi, . _ -)")
    toko = Toko(nama)
    if any(t.slug == toko.slug for t in semua_toko()):
        raise ValueError("Toko sudah ada")
    toko.dir.mkdir(parents=True, exist_ok=True)
    toko.simpan_pesan(PESAN_TEMPLATE)
    return toko


def toko_dari_slug(slug: str) -> Toko | None:
    return next((t for t in semua_toko() if t.slug == slug), None)


def cari_toko(nama: str) -> Toko:
    """Cocokkan nama toko tanpa peduli huruf besar/kecil."""
    kunci = nama.strip().lower()
    for t in semua_toko():
        if kunci in (t.nama.lower(), t.slug):
            return t
    raise SystemExit(f"Toko '{nama}' tidak dikenal. Pilihan: {', '.join(t.nama for t in semua_toko())}")


def siapkan_folder() -> None:
    STORES_DIR.mkdir(parents=True, exist_ok=True)
    for t in semua_toko():
        t.dir.mkdir(parents=True, exist_ok=True)


def baca_cookies(toko: Toko) -> list[dict]:
    """Baca cookies.json (list of dict hasil export). Cookie sesi (expires < 0) dibuang field expires-nya
    karena ditolak CDP bila dikirim apa adanya."""
    data = json.loads(toko.cookies_file.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list) or not data:
        raise ValueError(f"{toko.cookies_file} kosong/tidak valid")
    for c in data:
        if isinstance(c.get("expires"), (int, float)) and c["expires"] < 0:
            c.pop("expires")
    return data


def periksa_identitas(toko: Toko, seller_id: str) -> None:
    """Pastikan cookies.json memang milik toko ini: seller_id pertama disimpan ke store.json,
    lalu dibandingkan di run berikutnya dan terhadap toko lain (cegah cookie salah folder)."""
    for t in semua_toko():
        if t.nama != toko.nama and t.store_file.exists():
            if json.loads(t.store_file.read_text(encoding="utf-8")).get("seller_id") == seller_id:
                raise RuntimeError(f"seller_id {seller_id} ternyata milik toko '{t.nama}', bukan '{toko.nama}' "
                                   "- cookies.json salah folder?")
    if toko.store_file.exists():
        tersimpan = json.loads(toko.store_file.read_text(encoding="utf-8")).get("seller_id")
        if tersimpan != seller_id:
            raise RuntimeError(f"seller_id sesi ({seller_id}) != yang tersimpan untuk '{toko.nama}' ({tersimpan}). "
                               "Cookies diganti ke toko lain? Hapus store.json bila memang disengaja.")
    else:
        toko.store_file.write_text(json.dumps({"nama": toko.nama, "seller_id": seller_id}, indent=2), encoding="utf-8")
