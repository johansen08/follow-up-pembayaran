"""Pengaturan global UI: daftar inisial & inisial aktif (data/app.json)."""

from __future__ import annotations

import re
import threading

from .config import INISIAL_DEFAULT, ROOT
from .util import baca_json, tulis_json

FILE = ROOT / "data" / "app.json"
_POLA = re.compile(r"^[A-Za-z0-9]{1,6}$")
_kunci = threading.Lock()


def _bersih(nilai: str) -> str:
    """'~-f' / '-f' / ' f ' -> 'f'; ValueError bila tidak valid."""
    v = re.sub(r"^[~\-\s]+", "", str(nilai)).strip()
    if not _POLA.match(v):
        raise ValueError("Inisial 1-6 huruf/angka")
    return v


def baca() -> dict:
    d = baca_json(FILE, {})
    daftar = [x for x in d.get("inisial", INISIAL_DEFAULT) if isinstance(x, str)]
    aktif = d.get("aktif") if d.get("aktif") in daftar else (daftar[0] if daftar else "")
    return {"inisial": daftar, "aktif": aktif}


def _simpan(d: dict) -> dict:
    tulis_json(FILE, d)
    return d


def tambah(nilai: str) -> dict:
    v = _bersih(nilai)
    with _kunci:
        d = baca()
        if v in d["inisial"]:
            raise ValueError("Inisial sudah ada")
        d["inisial"].append(v)
        d["aktif"] = v
        return _simpan(d)


def hapus(nilai: str) -> dict:
    with _kunci:
        d = baca()
        d["inisial"] = [x for x in d["inisial"] if x != nilai]
        if d["aktif"] == nilai:
            d["aktif"] = d["inisial"][0] if d["inisial"] else ""
        return _simpan(d)


def pilih(nilai: str) -> dict:
    with _kunci:
        d = baca()
        if nilai not in d["inisial"]:
            raise ValueError("Inisial tidak ada")
        d["aktif"] = nilai
        return _simpan(d)
