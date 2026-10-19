"""Kirim pesan lewat UI chat TikTok Seller.

Pencegahan pesan ganda / salah kirim (berlapis):
  1. send_log.json: pesanan yang sudah ada di log tidak diproses lagi (lihat runner).
  2. IDENTITAS PERCAKAPAN: halaman chat bisa sempat menampilkan percakapan lain (mis. pembeli yang baru
     dikirimi) sebelum berpindah. Bot baru percaya halaman bila (a) panel info menampilkan ID pesanan ini,
     (b) header percakapan aktif memuat nama yang cocok dengan pembeli pesanan ini (huruf awal,
     huruf akhir, panjang; kartu terpilih di daftar, bila ada, harus sama), dan (c) daftar pesan ada. Jika tidak -> TIDAK mengirim.
  3. "Sudah ada" HANYA dibaca dari gelembung pesan kita (`.chatd-message--right pre`) di dalam daftar
     pesan (`im_message`), bukan dari seluruh halaman.
  4. Riwayat harus selesai termuat: teks stabil dan penanda "Tidak ada pesan sebelumnya" tampil
     (kecuali pesan kita sudah ketemu).
  5. Status 'mencoba' dicatat ke log sebelum mengetik, jadi crash setelah Enter pun tidak mengulang.
"""

from __future__ import annotations

import json
import re
import time
from typing import Callable

from .config import BASE_URL, INPUT_SELECTORS

# Hasil kirim_lewat_ui
SUDAH_ADA = "sudah_ada"        # pesan sama sudah ada di percakapan (tidak dikirim lagi)
TERKIRIM = "terkirim"          # terbukti muncul di percakapan
BELUM_KETIK = "belum_ketik"    # gagal sebelum mengetik apa pun / percakapan tak terverifikasi (aman dicoba lagi)
TIDAK_PASTI = "tidak_pasti"    # Enter sudah ditekan tapi tidak terverifikasi (JANGAN kirim ulang otomatis)
PERLU_KIRIM = "perlu_kirim"    # hanya dry-run: pesan belum ada di percakapan, akan dikirim bila --kirim

PANJANG_KUNCI = 40             # jumlah karakter awal pesan yang dicocokkan dengan gelembung pesan kita
TEKS_AWAL_RIWAYAT = "Tidak ada pesan sebelumnya"

# Membaca keadaan halaman chat dalam satu panggilan. Pembeli dicocokkan lewat pola nama karena nama di
# daftar percakapan tidak disamarkan sedangkan nama dari daftar pesanan disamarkan (awal + * + akhir).
_JS_STATE = r"""
const oid = arguments[0];
const norm = s => (s||'').replace(/\s+/g,' ').trim();
const teks = norm(document.body.innerText);
const root = document.querySelector('[data-log_page_name="im_message"]');
const pola = n => { const a = [...norm(n)]; return [a.length ? a[0] : '', a.length ? a[a.length-1] : '', a.length]; };
const kartu = [...document.querySelectorAll('[data-testid="chat.chatroom.conversation_card"]')];
const terpilih = kartu.filter(k => { const c = getComputedStyle(k).backgroundColor; return c && c !== 'rgba(0, 0, 0, 0)' && c !== 'transparent'; });
const namaKartu = k => { const u = k.querySelector('[data-testid="chat.chatroom.conversation_card_username"]'); return u ? u.textContent : ''; };
// header percakapan aktif (topbar): naik dari tombol bintang sampai ketemu ancestor yang memuat teks pendek (nama)
let header = [];
const bintang = document.querySelector('[data-testid="chat.action.chatroom.topbar.star"]');
if (bintang) {
  let anc = bintang;
  for (let i = 0; i < 6 && anc.parentElement && !header.length; i++) {
    anc = anc.parentElement;
    const w = document.createTreeWalker(anc, NodeFilter.SHOW_TEXT); let n;
    while ((n = w.nextNode())) { const t = norm(n.textContent); if (t && t.length <= 60) header.push(pola(t)); }
  }
}
return JSON.stringify({
  header_pola: header,
  teks_len: teks.length,
  oid_ada: teks.includes(oid),
  root_ada: !!root,
  pesan_kita: root ? [...root.querySelectorAll('.chatd-message--right pre')].map(e => norm(e.textContent)) : [],
  riwayat_lengkap: !!root && [...root.querySelectorAll('.p-divider-text')].some(e => norm(e.textContent) === '""" + TEKS_AWAL_RIWAYAT + r"""'),
  kartu_terpilih: terpilih.map(k => pola(namaKartu(k))),
});
"""


def baca_state(tab, oid: str) -> dict:
    return json.loads(tab.run_js(_JS_STATE, oid))


def _normal(teks: str) -> str:
    return re.sub(r"\s+", " ", teks or "").strip()


def pola_nama(nama: str) -> list:
    """[huruf awal, huruf akhir, panjang] (per karakter Unicode) - sama dengan yang dihitung _JS_STATE."""
    h = list(_normal(nama))
    return [h[0] if h else "", h[-1] if h else "", len(h)]


def _seragam(pola) -> list:
    return [x.lower() if isinstance(x, str) else x for x in pola]


def identitas_cocok(state: dict, pesanan: dict) -> str | None:
    """None bila halaman terbukti menampilkan percakapan pesanan ini; selain itu alasan penolakan."""
    pembeli = pesanan.get("pembeli") or ""
    if not state.get("root_ada"):
        return "daftar pesan tidak ditemukan"
    if not state.get("oid_ada"):
        return f"ID pesanan {pesanan['order_id']} belum tampil"
    if _normal(pembeli) in ("", "?"):
        return "nama pembeli tidak diketahui, percakapan tidak bisa diverifikasi"
    target = _seragam(pola_nama(pembeli))
    header = state.get("header_pola") or []
    if not header:
        return "header percakapan (nama pembeli) tidak ditemukan"
    if target not in [_seragam(p) for p in header]:
        return "percakapan yang tampil bukan milik pembeli pesanan ini"
    terpilih = state.get("kartu_terpilih") or []
    if len(terpilih) == 1 and _seragam(terpilih[0]) != target:  # penanda tambahan bila kartu aktif ada di daftar
        return "kartu percakapan terpilih bukan milik pembeli pesanan ini"
    return None


def pesan_kita_ada(state: dict, pesan: str) -> bool:
    kunci = _normal(pesan)[:PANJANG_KUNCI]
    return bool(kunci) and any(kunci in _normal(t) for t in state.get("pesan_kita", []))


def _cari_input(tab, tunggu: float = 15.0):
    """Cari kotak input chat; halaman chat kadang lambat termuat, jadi coba terus sampai `tunggu` detik."""
    batas = time.monotonic() + tunggu
    while True:
        for sel in INPUT_SELECTORS:
            el = tab.ele(sel, timeout=1)
            if el:
                return el
        if time.monotonic() >= batas:
            return None


def halaman_siap(tab, pesanan: dict, tunggu: float = 20.0,
                 tidur: Callable[[float], None] | None = None, jam: Callable[[], float] | None = None) -> str | None:
    """Tunggu sampai halaman terbukti menampilkan percakapan pesanan ini. None = siap; selain itu alasan terakhir."""
    tidur, jam = tidur or time.sleep, jam or time.monotonic
    mulai = jam()
    while True:
        alasan = identitas_cocok(baca_state(tab, pesanan["order_id"]), pesanan)
        if alasan is None:
            return None
        if jam() - mulai >= tunggu:
            return alasan
        tidur(0.5)


def riwayat_termuat(tab, min_s: float = 3.0, stabil_s: float = 2.5, maks_s: float = 20.0,
                    tidur: Callable[[float], None] | None = None, jam: Callable[[], float] | None = None) -> bool:
    """Tunggu sampai teks halaman berhenti berubah `stabil_s` detik (riwayat chat selesai termuat).
    False bila sampai `maks_s` detik masih berubah -> riwayat tidak bisa dipastikan."""
    tidur, jam = tidur or time.sleep, jam or time.monotonic
    mulai = jam()
    terakhir_ubah = mulai
    panjang = -1
    while True:
        tidur(0.5)
        sekarang = jam()
        p = len(tab.run_js("return document.body.innerText") or "")
        if p != panjang:
            panjang, terakhir_ubah = p, sekarang
        if sekarang - mulai >= min_s and sekarang - terakhir_ubah >= stabil_s:
            return True
        if sekarang - mulai >= maks_s:
            return False


def _periksa(tab, pesanan: dict, pesan: str):
    """Return (kotak input, pesan sudah ada di percakapan). Kotak None bila input tidak ditemukan atau
    percakapan/riwayat tidak terverifikasi (dalam semua kasus itu JANGAN mengirim)."""
    oid = pesanan["order_id"]
    box = _cari_input(tab)
    if not box:
        print("   ! kotak input chat tidak ditemukan")
        return None, False
    alasan = halaman_siap(tab, pesanan)
    if alasan:
        print(f"   ! {alasan}, tidak dikirim")
        return None, False
    if not riwayat_termuat(tab):
        print("   ! riwayat chat belum selesai termuat, tidak dikirim demi mencegah pesan ganda")
        return None, False
    state = baca_state(tab, oid)
    alasan = identitas_cocok(state, pesanan)  # halaman bisa berpindah percakapan saat memuat
    if alasan:
        print(f"   ! halaman berubah selama memuat ({alasan}), tidak dikirim")
        return None, False
    if pesan_kita_ada(state, pesan):
        return box, True
    if not state.get("riwayat_lengkap"):
        print("   ! riwayat lama belum termuat penuh, tidak bisa memastikan pesan belum pernah dikirim, tidak dikirim")
        return None, False
    return box, False


def _kotak_siap(tab, tunggu: float = 10.0):
    """Cari ulang kotak input sampai benar-benar tampil & bisa diklik (klik hanya memfokuskan, tidak mengirim).
    Dipanggil SEBELUM log 'mencoba' ditulis: kegagalan di sini tidak mengunci pesanan. None bila tak kunjung siap."""
    try:
        tab.set.activate()  # tab di latar bisa belum punya layout -> elemen "tidak punya lokasi/ukuran"
    except Exception:
        pass
    batas = time.monotonic() + tunggu
    while True:
        box = _cari_input(tab, tunggu=2)
        if box:
            try:
                box.click()
                return box
            except Exception as e:
                print(f"   ! kotak input belum bisa diklik ({' '.join(str(e).split())[:60]}), coba lagi")
        if time.monotonic() >= batas:
            return None
        time.sleep(0.5)


def periksa_lewat_ui(browser, pesanan: dict, pesan: str) -> str:
    """DRY-RUN: buka chat & cek riwayat saja. Tidak mengetik, tidak menekan Enter, tidak menulis log.
    `pesanan` = dict dengan order_id, pembeli, chat_link.
    Return PERLU_KIRIM / SUDAH_ADA / BELUM_KETIK (input tidak ditemukan / percakapan tak terverifikasi)."""
    tab = browser.new_tab(BASE_URL + pesanan["chat_link"])
    try:
        box, ada = _periksa(tab, pesanan, pesan)
        if not box:
            return BELUM_KETIK
        return SUDAH_ADA if ada else PERLU_KIRIM
    finally:
        tab.close()


def kirim_lewat_ui(browser, pesanan: dict, pesan: str, sebelum_ketik: Callable[[], None]) -> str:
    """Buka chat pesanan, ketik pesan, Enter, verifikasi. `sebelum_ketik` dipanggil tepat sebelum
    mengetik (untuk mencatat 'mencoba' ke log). `pesanan` = dict dengan order_id, pembeli, chat_link."""
    oid = pesanan["order_id"]
    tab = browser.new_tab(BASE_URL + pesanan["chat_link"])
    try:
        box, ada = _periksa(tab, pesanan, pesan)
        if not box:
            return BELUM_KETIK
        if ada:
            return SUDAH_ADA
        box = _kotak_siap(tab)  # cari ulang: elemen lama bisa sudah diganti saat halaman dirender ulang
        if not box:
            print("   ! kotak input chat tidak bisa diklik, tidak dikirim (aman dicoba lagi)")
            return BELUM_KETIK
        alasan = identitas_cocok(baca_state(tab, oid), pesanan)  # cek terakhir: jangan mengetik di percakapan lain
        if alasan:
            print(f"   ! halaman berpindah ({alasan}), tidak dikirim")
            return BELUM_KETIK
        sebelum_ketik()  # titik tanpa jalan kembali: mulai dari sini pesanan dianggap sudah dicoba
        box.input(pesan, clear=True)
        time.sleep(0.5)
        tab.actions.key_down("ENTER").key_up("ENTER")
        for _ in range(10):
            time.sleep(1)
            state = baca_state(tab, oid)
            if identitas_cocok(state, pesanan) is None and pesan_kita_ada(state, pesan) \
                    and not (box.text or box.value or "").strip():
                return TERKIRIM
        # Cek akhir lebih lama: pesan bisa muncul terlambat atau kotak input belum kosong. Sebelum mengetik
        # pesan kita terbukti belum ada, jadi gelembung kita di percakapan terverifikasi ini berarti terkirim.
        for _ in range(8):
            time.sleep(1)
            state = baca_state(tab, oid)
            if identitas_cocok(state, pesanan) is None and pesan_kita_ada(state, pesan):
                return TERKIRIM
        return TIDAK_PASTI
    finally:
        tab.close()
