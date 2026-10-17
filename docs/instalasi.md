# Instalasi

## Prasyarat

- Windows
- Python 3.10 atau lebih baru, sudah masuk `PATH`
  (dari <https://www.python.org/downloads/>, centang "Add python.exe to PATH")
- Google Chrome (bot memakai Chrome asli, bukan Chromium)
- Koneksi internet untuk memasang dependensi

## Cara cepat

Klik dua kali `instalasi.bat`. Skrip ini:

1. Mencari Python dan menolak versi di bawah 3.10.
2. Menjalankan `pip install -r requirements.txt`, lalu memastikan DrissionPage bisa dimuat.
3. Menyiapkan folder `data\stores` untuk setiap toko.
4. Memeriksa Google Chrome (hanya peringatan bila tidak ada).

Skrip tidak mengubah versi pip dan memasang ke Python yang ditemukan di `PATH`.

## Cara manual

```bash
pip install -r requirements.txt
```

## Dependensi

| Paket | Fungsi |
|---|---|
| `DrissionPage` | Mengendalikan Chrome (diuji dengan 4.1.1.2) |

## Memastikan berhasil

```bash
python main.py --help
```

Bila bantuan perintah tampil, instalasi berhasil.

Lanjut ke [penggunaan.md](penggunaan.md).
