"""CLI: python fu_pembayaran.py [--toko NAMA ...] [--kirim] [--limit N] [--pesan TEKS]"""

from __future__ import annotations

import argparse

from .config import PESAN_DEFAULT
from .runner import jalankan_toko
from .stores import cari_toko, semua_toko, siapkan_folder


def main() -> None:
    ap = argparse.ArgumentParser(description="Follow-up pembayaran TikTok Seller (default: DRY-RUN)")
    ap.add_argument("--toko", action="append", metavar="NAMA",
                    help=f"nama toko (boleh berulang); default: semua yang punya cookies.json. Pilihan: {', '.join(t.nama for t in semua_toko()) or '(belum ada, tambahkan lewat UI)'}")
    ap.add_argument("--kirim", action="store_true", help="benar-benar kirim pesan (default dry-run)")
    ap.add_argument("--limit", type=int, default=0, help="maks. pesan per toko (0 = semua)")
    ap.add_argument("--pesan", default=PESAN_DEFAULT, help="ganti teks pesan")
    args = ap.parse_args()

    siapkan_folder()
    daftar = [cari_toko(n) for n in args.toko] if args.toko else [t for t in semua_toko() if t.siap()]
    if not daftar:
        raise SystemExit("Tidak ada toko dengan cookies.json di data/stores/<nama_toko>/")

    for toko in daftar:
        try:
            jalankan_toko(toko, args.kirim, args.limit, args.pesan)
        except Exception as e:  # satu toko gagal tidak menghentikan toko lain
            print(f"[ERROR] {toko.nama}: {e}")
