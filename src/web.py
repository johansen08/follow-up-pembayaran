"""Server web lokal: python -m src.web  ->  http://127.0.0.1:8765

Hanya melayani localhost. Semua request yang mengubah data wajib membawa header `X-FU: 1`
dan (bila ada) Origin/Host harus lokal, supaya halaman web lain tidak bisa memicu pengiriman.
"""

from __future__ import annotations

import json
import re
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from . import logs, settings
from .config import ROOT, WEB_HOST, WEB_PORT
from .login import LoginManager
from .service import RunManager, SedangJalan
from .stores import Toko, semua_toko, siapkan_folder, tambah_toko, toko_dari_slug
from .util import baca_json

INDEX = ROOT / "web" / "index.html"
MANAGER = RunManager()
LOGIN = LoginManager()
MAKS_BODY = 64 * 1024
MAKS_PESAN = 1500


def render_pesan(toko: Toko, inisial: str) -> str:
    return toko.pesan().replace("{toko}", toko.nama).replace("{inisial}", inisial)


def _status_log(status: str, cur: dict | None, slug: str, no: str) -> str | None:
    """Status log berkas -> status UI. None = tidak ditampilkan (mis. sudah_ada_di_chat)."""
    if status == "terkirim":
        return "terkirim"
    if status == "mencoba":  # sedang diproses bila memang itu pesanan yang aktif, selain itu gagal di tengah jalan
        return "mencoba" if cur and cur["toko"] == slug and cur["no"] == no else "perlu_dicek"
    if status == "tidak_pasti":
        return "perlu_dicek"
    return None


def data_state() -> dict:
    return {
        "stores": [{"id": t.slug, "nama": t.nama, "siap": t.siap(), "pesan": t.pesan()} for t in semua_toko()],
        **settings.baca(),
    }


def data_log() -> list[dict]:
    snap = MANAGER.snapshot()
    cur = snap["cur"] if snap else None
    out = []
    for t in semua_toko():
        if not t.log_file.exists():
            continue
        for no, e in baca_json(t.log_file, {}).items():
            st = _status_log(e.get("status", ""), cur, t.slug, no)
            if st:  # nama pembeli sengaja tidak dikirim ke UI
                out.append({"toko": t.slug, "no": no, "status": st, "waktu": e.get("waktu", "")})
    out.sort(key=lambda x: x["waktu"], reverse=True)
    return out[:1000]


class Galat(Exception):
    def __init__(self, kode: int, pesan: str):
        self.kode, self.pesan = kode, pesan


def _toko(slug: str) -> Toko:
    t = toko_dari_slug(slug)
    if not t:
        raise Galat(404, "Toko tidak ditemukan")
    return t


def _pesan_valid(teks) -> str:
    if not isinstance(teks, str) or not teks.strip():
        raise Galat(400, "Pesan tidak boleh kosong")
    if len(teks) > MAKS_PESAN:
        raise Galat(400, f"Pesan maksimal {MAKS_PESAN} karakter")
    asing = sorted(set(re.findall(r"\{[^{}]*\}", teks)) - {"{toko}", "{inisial}"})
    if asing:  # variabel tak dikenal akan terkirim apa adanya ke pembeli
        raise Galat(400, "Variabel tidak dikenal: " + ", ".join(asing) + " (hanya {toko} dan {inisial})")
    return teks


def api(metode: str, path: str, body: dict) -> tuple[int, dict]:
    """Router API murni (mudah diuji tanpa HTTP)."""
    m = re.fullmatch(r"/api/stores/([a-z0-9_.\-]+)/(pesan|login)", path)
    if metode == "GET" and path == "/api/state":
        return 200, data_state()
    if metode == "GET" and path == "/api/run":
        return 200, {"run": MANAGER.snapshot()}
    if metode == "GET" and path == "/api/log":
        return 200, {"log": data_log()}
    if metode == "POST" and path == "/api/stores":
        try:
            t = tambah_toko(body.get("nama", ""))
        except ValueError as e:
            raise Galat(400, str(e))
        return 200, {"id": t.slug}
    if metode == "PUT" and m and m.group(2) == "pesan":
        _toko(m.group(1)).simpan_pesan(_pesan_valid(body.get("pesan")))
        return 200, {"ok": True}
    if metode == "POST" and path == "/api/pesan-semua":
        teks = _pesan_valid(body.get("pesan"))
        for t in semua_toko():
            t.simpan_pesan(teks)
        return 200, {"ok": True}
    if metode == "POST" and m and m.group(2) == "login":
        try:
            LOGIN.mulai(_toko(m.group(1)), run_aktif=MANAGER.aktif())
        except RuntimeError as e:
            raise Galat(409, str(e))
        return 200, {"ok": True}
    if metode == "GET" and path == "/api/login":
        return 200, {"login": LOGIN.snapshot()}
    if metode == "POST" and path == "/api/login/batal":
        LOGIN.batal()
        return 200, {"ok": True}
    try:
        if metode == "POST" and path == "/api/inisial":
            return 200, settings.tambah(body.get("nilai", ""))
        if metode == "PUT" and path == "/api/inisial/aktif":
            return 200, settings.pilih(body.get("nilai", ""))
        mi = re.fullmatch(r"/api/inisial/([A-Za-z0-9]{1,6})", path)
        if metode == "DELETE" and mi:
            return 200, settings.hapus(mi.group(1))
    except ValueError as e:
        raise Galat(400, str(e))
    if metode == "POST" and path == "/api/run":
        slugs = body.get("toko")
        if not isinstance(slugs, list) or not slugs:
            raise Galat(400, "Pilih minimal satu toko")
        daftar = [_toko(s) for s in dict.fromkeys(slugs)]
        belum = [t.nama for t in daftar if not t.siap()]
        if belum:
            raise Galat(400, "Belum login: " + ", ".join(belum))
        aktif = settings.baca()["aktif"]
        if not aktif:
            raise Galat(400, "Pilih inisial dulu")
        for t in daftar:
            _pesan_valid(t.pesan())
        if LOGIN.aktif():  # login & bot memakai port Chrome yang sama
            raise Galat(409, "Login toko sedang berlangsung, selesaikan dulu")
        try:
            MANAGER.mulai(daftar, lambda t: render_pesan(t, aktif))
        except SedangJalan as e:
            raise Galat(409, str(e))
        return 200, {"ok": True}
    if metode == "POST" and path == "/api/run/stop":
        MANAGER.hentikan()
        return 200, {"ok": True}
    raise Galat(404, "Tidak ditemukan")


class Handler(BaseHTTPRequestHandler):
    server_version = "FU"

    def log_message(self, *a):  # senyap
        pass

    def _kirim(self, kode: int, data: bytes, tipe: str) -> None:
        self.send_response(kode)
        self.send_header("Content-Type", tipe)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _json(self, kode: int, obj) -> None:
        self._kirim(kode, json.dumps(obj, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def _lokal(self) -> bool:
        port = self.server.server_address[1]
        sah = {f"127.0.0.1:{port}", f"localhost:{port}"}
        if self.headers.get("Host", "") not in sah:  # tolak DNS rebinding
            return False
        origin = self.headers.get("Origin")
        return origin is None or origin in {f"http://{h}" for h in sah}

    def _tangani(self, metode: str) -> None:
        path = urlparse(self.path).path
        if not self._lokal():
            return self._json(403, {"error": "Ditolak"})
        if metode == "GET" and not path.startswith("/api/"):
            if path in ("/", "/index.html") and INDEX.exists():
                return self._kirim(200, INDEX.read_bytes(), "text/html; charset=utf-8")
            return self._json(404, {"error": "Tidak ditemukan"})
        if metode != "GET" and self.headers.get("X-FU") != "1":
            return self._json(403, {"error": "Header X-FU wajib"})
        try:
            n = int(self.headers.get("Content-Length") or 0)
            if n > MAKS_BODY:
                return self._json(413, {"error": "Terlalu besar"})
            body = json.loads(self.rfile.read(n) or b"{}") if n else {}
            if not isinstance(body, dict):
                raise ValueError
            kode, data = api(metode, path, body)
        except Galat as g:
            return self._json(g.kode, {"error": g.pesan})
        except ValueError:
            return self._json(400, {"error": "JSON tidak valid"})
        except Exception as e:  # jangan bocorkan stack trace
            logs.galat(f"web {metode} {path}", e)
            return self._json(500, {"error": "Kesalahan server"})
        self._json(kode, data)

    def do_GET(self): self._tangani("GET")
    def do_POST(self): self._tangani("POST")
    def do_PUT(self): self._tangani("PUT")
    def do_DELETE(self): self._tangani("DELETE")


def main(buka_browser: bool = True) -> None:
    siapkan_folder()
    logs.aktifkan()
    srv = ThreadingHTTPServer((WEB_HOST, WEB_PORT), Handler)
    url = f"http://{WEB_HOST}:{WEB_PORT}"
    print(f"FU Pembayaran berjalan di {url}  (Ctrl+C untuk berhenti)")
    if buka_browser:
        webbrowser.open(url)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        MANAGER.hentikan()
        LOGIN.batal()
        srv.server_close()


if __name__ == "__main__":
    main()
