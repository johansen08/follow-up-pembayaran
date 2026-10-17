"""Log pesanan yang sudah di-FU (per toko). Keberadaan order_id di log = JANGAN dikirim lagi."""

from __future__ import annotations

import json
from datetime import datetime

from .stores import Toko
from .util import ganti_berkas


class LogKirim:
    def __init__(self, toko: Toko):
        self._file = toko.log_file
        self._data: dict[str, dict] = {}
        if self._file.exists():
            try:
                self._data = json.loads(self._file.read_text(encoding="utf-8"))
            except Exception:
                # sengaja raise (bukan sys.exit): thread UI web tidak boleh mati diam-diam
                raise RuntimeError(f"{self._file} rusak, toko ini dihentikan agar tidak kirim ganda. "
                                   "Periksa/perbaiki berkas itu secara manual.")

    def __contains__(self, order_id: str) -> bool:
        return order_id in self._data

    def __len__(self) -> int:
        return len(self._data)

    def catat(self, order_id: str, status: str, pembeli: str) -> None:
        self._data[order_id] = {
            "status": status,
            "waktu": datetime.now().isoformat(timespec="seconds"),
            "pembeli": pembeli,
        }
        self._simpan()

    def ubah_status(self, order_id: str, status: str) -> None:
        self._data[order_id]["status"] = status
        self._simpan()

    def _simpan(self) -> None:
        tmp = self._file.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._data, ensure_ascii=False, indent=2), encoding="utf-8")
        ganti_berkas(tmp, self._file)
