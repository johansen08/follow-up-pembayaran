"""Helper kecil: baca/tulis JSON secara atomik."""

from __future__ import annotations

import json
import time
from pathlib import Path


def ganti_berkas(tmp: Path, tujuan: Path) -> None:
    """tmp -> tujuan secara atomik. Di Windows replace() ditolak (PermissionError) selama berkas
    tujuan sedang dibuka pembaca lain (mis. UI yang polling log), jadi coba lagi sebentar."""
    for i in range(40):
        try:
            tmp.replace(tujuan)
            return
        except PermissionError:
            if i == 39:
                raise
            time.sleep(0.05)


def baca_json(path: Path, default):
    for i in range(20):
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (FileNotFoundError, ValueError):
            return default
        except PermissionError:  # Windows: berkas sedang diganti penulis lain, coba lagi sebentar
            if i == 19:
                raise
            time.sleep(0.025)


def tulis_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    ganti_berkas(tmp, path)
