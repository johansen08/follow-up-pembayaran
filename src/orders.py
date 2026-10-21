"""Ambil pesanan belum bayar dari halaman pesanan TikTok Seller."""

from __future__ import annotations

import json
import time
from urllib.parse import parse_qs, urlparse

from . import logs
from .config import ORDER_URL, PAGE_SIZE, STATUS_BELUM_BAYAR

# Dipakai bila DrissionPage tidak memberi body request asli: body tab "pending" dari hasil sniff.
BODY_PENDING = {
    "search_condition": {"condition_list": {"search_tab": {"value": ["110"]}}},
    "sort_info": "6",
    "pagination_type": 0,
}

_FETCH_JS = (
    "return fetch(arguments[0],{method:'POST',credentials:'include',"
    "headers:{'content-type':'application/json','x-tt-oec-region':'ID'},"
    "body:arguments[1]}).then(r=>r.json())"
)


def ambil_pesanan_belum_bayar(tab, percobaan: int = 3) -> tuple[str, list[dict]]:
    """Ambil daftar pesanan; gangguan sesaat (halaman berpindah, 'searchId', request tak tertangkap)
    diulang `percobaan` kali. Aman diulang: hanya membaca."""
    for ke in range(1, percobaan + 1):
        try:
            return _ambil(tab)
        except Exception as e:
            if ke == percobaan:
                raise
            print(f"[fu] gagal ambil daftar pesanan ({type(e).__name__}: {' '.join(str(e).split())[:80]}), "
                  f"percobaan {ke}/{percobaan}")
            logs.galat(f"ambil daftar pesanan percobaan {ke}/{percobaan}", e)
            time.sleep(3)


def _ambil(tab) -> tuple[str, list[dict]]:
    """Return (seller_id, daftar pesanan belum bayar). Tangkap request order/list pertama dari halaman
    (agar parameter URL ikut), lalu paginasi dengan fetch di konteks halaman."""
    tab.listen.start("api/fulfillment/order/list", method="POST")
    tab.get(ORDER_URL)
    paket = tab.listen.wait(timeout=30)
    tab.listen.stop()
    if not paket:
        raise RuntimeError("request order/list tidak tertangkap - cek login/cookies")

    url = paket.url
    seller_id = parse_qs(urlparse(url).query).get("seller_id", [""])[0]
    raw = paket.request.postData
    if isinstance(raw, str):
        raw = json.loads(raw)
    body = dict(raw) if isinstance(raw, dict) else dict(BODY_PENDING)

    orders, offset = [], 0
    while True:
        body.update({"offset": offset, "count": PAGE_SIZE})
        data = tab.run_js(_FETCH_JS, url, json.dumps(body))
        if data.get("code") != 0:
            raise RuntimeError(f"order/list gagal: {data.get('message')}")
        isi = data.get("data") or {}
        page = isi.get("main_orders") or []
        orders += page
        offset += len(page)
        total = isi.get("total_count")
        # Halaman > 1 selalu dicek: lanjut selama halaman terisi penuh / belum mencapai total / server bilang masih ada.
        if not page:
            break
        if total is not None and offset >= total and not isi.get("has_more"):
            break
        if total is None and len(page) < PAGE_SIZE and not isi.get("has_more"):
            break

    hasil = []
    for o in orders:
        status = {s["main_order_status"] for s in o.get("order_status_module", [])}
        if STATUS_BELUM_BAYAR not in status:
            continue
        hasil.append({
            "order_id": o["main_order_id"],
            "pembeli": o.get("buyer_info_module", {}).get("buyer_nickname", "?"),
            "total": o.get("price_module", {}).get("grand_total", {}).get("format_price", "?"),
            "chat_link": o.get("action_module", {}).get("buyer_im_action_link"),
        })
    return seller_id, hasil
