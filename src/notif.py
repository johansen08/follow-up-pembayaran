"""Pop-up peringatan + suara saat proses terhenti / butuh tindakan user (mis. captcha).

Pop-up dibuat di thread sendiri (tidak memblokir run), selalu di atas jendela lain (jendela Chrome
tidak menutupinya), dan menutup sendiri setelah `DETIK_TUTUP` detik. Gagal membuka pop-up/suara
tidak boleh pernah mengganggu run, jadi semua kesalahan ditelan.
"""

from __future__ import annotations

import gc
import threading
import time

try:
    import winsound  # hanya Windows
except ImportError:  # pragma: no cover
    winsound = None

DETIK_TUTUP = 10
_kunci = threading.Lock()  # satu pop-up pada satu waktu; yang lain antre


def bunyi(selesai: threading.Event | None = None) -> None:
    """Bunyikan alarm (dua nada) berulang tiap ~2 detik sampai `selesai` di-set / maksimal DETIK_TUTUP."""
    if winsound is None:
        return
    batas = time.monotonic() + DETIK_TUTUP
    try:
        while time.monotonic() < batas and not (selesai and selesai.is_set()):
            winsound.Beep(1000, 300)
            winsound.Beep(1300, 400)
            if selesai:
                selesai.wait(1.5)
            else:
                break
    except Exception:
        pass


def _tampilkan(judul: str, pesan: str, detik: int) -> None:
    import tkinter as tk

    selesai = threading.Event()
    with _kunci:
        root = tk.Tk()
        root.title(judul)
        root.attributes("-topmost", True)
        root.resizable(False, False)
        root.configure(bg="#fee2e2")
        tk.Label(root, text=f"⚠  {judul}", font=("Segoe UI", 13, "bold"), fg="#b91c1c", bg="#fee2e2",
                 anchor="w").pack(fill="x", padx=18, pady=(16, 4))
        tk.Label(root, text=pesan, font=("Segoe UI", 10), bg="#fee2e2", fg="#16191f", justify="left",
                 wraplength=380, anchor="w").pack(fill="x", padx=18)
        hitung = tk.Label(root, font=("Segoe UI", 9), bg="#fee2e2", fg="#667085", anchor="w")
        hitung.pack(fill="x", padx=18, pady=(10, 0))
        tk.Button(root, text="Tutup", width=10, command=root.destroy).pack(anchor="e", padx=18, pady=(6, 14))

        root.update_idletasks()  # posisi: pojok kanan bawah layar, di atas taskbar
        x = root.winfo_screenwidth() - root.winfo_reqwidth() - 24
        y = root.winfo_screenheight() - root.winfo_reqheight() - 72
        root.geometry(f"+{x}+{y}")
        root.lift()
        root.focus_force()

        def tik(sisa: int) -> None:
            if sisa <= 0:
                root.destroy()
                return
            hitung.config(text=f"Menutup otomatis dalam {sisa} detik")
            root.after(1000, tik, sisa - 1)

        threading.Thread(target=bunyi, args=(selesai,), daemon=True).start()
        tik(detik)
        try:
            root.mainloop()
        finally:
            selesai.set()
            try:
                root.destroy()
            except Exception:
                pass
            del root, hitung
            gc.collect()  # Tk harus dibuang di thread yang membuatnya, kalau tidak Tcl_AsyncDelete crash


def peringatan(judul: str, pesan: str, detik: int = DETIK_TUTUP) -> None:
    """Munculkan pop-up + suara, kembali segera (tidak menunggu pop-up ditutup)."""
    def kerja() -> None:
        try:
            _tampilkan(judul, pesan, detik)
        except Exception:  # tkinter tak terpasang / tak ada layar: minimal tetap berbunyi
            bunyi()

    threading.Thread(target=kerja, name="popup-peringatan", daemon=True).start()
