"""Konstanta & daftar toko."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STORES_DIR = ROOT / "data" / "stores"

# Toko bawaan (opsional). Biasanya dikosongkan: toko ditambahkan lewat UI (＋ Tambah toko) dan
# tersimpan di data/stores/<nama-toko>/meta.json, yang diabaikan Git.
TOKO: list[str] = []

BASE_URL = "https://seller-id.tokopedia.com"
ORDER_URL = f"{BASE_URL}/order?selected_sort=6&tab=pending"
LOCAL_PORT = 19223
STATUS_BELUM_BAYAR = 100
PAGE_SIZE = 50

# Jeda acak antar pesan (detik) agar tidak terlihat seperti bot.
JEDA_MIN, JEDA_MAX = 8, 20

# Teks persis seperti yang tertangkap di sniff (akhiran "~-f" = inisial).
PESAN_DEFAULT = (
    "halo, pesanan kamu sudah siap kirim jika kamu Segera lakukan pembayaran! "
    "lakukan pembayaran sebelum jm 12:00 ya spy pesanan kamu bisa di proses hari ini juga :D "
    "jangan sampai kehabisan stok nya ya!~-f"
)

# Template pesan default per toko untuk UI web. Variabel: {toko}, {inisial}.
PESAN_TEMPLATE = PESAN_DEFAULT[: -len("~-f")] + "~-{inisial}"
INISIAL_DEFAULT = ["f"]

# Server web (hanya lokal).
WEB_HOST = "127.0.0.1"
WEB_PORT = 8765

# Kandidat selector kotak input chat (urut dari paling spesifik).
INPUT_SELECTORS = [
    "css:textarea",
    "css:div[contenteditable='true']",
    "css:[contenteditable='plaintext-only']",
]
