"""Ambil pesanan belum bayar dari halaman pesanan TikTok Seller."""

from __future__ import annotations

import json
from urllib.parse import parse_qs, urlparse

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


def ambil_pesanan_belum_bayar(tab) -> tuple[str, list[dict]]:
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
        page = data["data"].get("main_orders", [])
        orders += page
        offset += len(page)
        if not page or offset >= data["data"].get("total_count", 0):
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
