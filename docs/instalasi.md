# Instalasi

Panduan dari nol sampai aplikasi siap dipakai. Hanya Windows.

## 1. Unduh dan pasang alat yang dibutuhkan

| Alat | Unduh | Catatan |
|---|---|---|
| **Git** | <https://git-scm.com/download/win> | Pilihan bawaan saat instalasi sudah cukup |
| **Python 3.10+** | <https://www.python.org/downloads/windows/> | **Centang "Add python.exe to PATH"** di layar pertama instalasi |
| **Google Chrome** | <https://www.google.com/chrome/> | Bot memakai Chrome asli, bukan Chromium |

Setelah terpasang, buka **Command Prompt** baru dan pastikan keduanya dikenali:

```bash
git --version
python --version
```

Bila `python` tidak dikenali, pasang ulang Python dan pastikan "Add python.exe to PATH" dicentang.

## 2. Clone repo

Pilih folder tujuan (misalnya `C:\`), buka Command Prompt di sana, lalu:

```bash
git clone https://github.com/johansen08/follow-up-pembayaran.git
cd follow-up-pembayaran
```

## 3. Klik `instalasi.bat`

Di folder `follow-up-pembayaran`, klik dua kali **`instalasi.bat`** (sekali saja). Skrip ini:

1. Mencari Python dan menolak versi di bawah 3.10.
2. Menjalankan `pip install -r requirements.txt`, lalu memastikan DrissionPage bisa dimuat.
3. Menyiapkan folder data toko.
4. Memeriksa Google Chrome (hanya peringatan bila tidak ada).

Skrip tidak mengubah versi pip dan memasang ke Python yang ditemukan di `PATH`.
Bila muncul `[GAGAL]`, baca pesannya, perbaiki, lalu jalankan ulang.

## 4. Jalankan aplikasi

Klik dua kali **`follow_up_pembayaran.bat`**. Browser terbuka ke <http://127.0.0.1:8765>.
Lanjut ke [penggunaan.md](penggunaan.md).

## Memperbarui ke versi terbaru

```bash
cd follow-up-pembayaran
git pull
```

Jalankan `instalasi.bat` lagi bila `requirements.txt` berubah. Folder `data\` (cookies, log, template)
tidak ikut Git dan tidak tertimpa.

## Cara manual (tanpa `instalasi.bat`)

```bash
pip install -r requirements.txt
```

| Paket | Fungsi |
|---|---|
| `DrissionPage` | Mengendalikan Chrome (diuji dengan 4.1.1.2) |

## Memastikan berhasil

```bash
python main.py --help
```

Bila bantuan perintah tampil, instalasi berhasil.
