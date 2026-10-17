# Follow Up Pembayaran

Aplikasi lokal untuk mengirim pesan pengingat pembayaran ke pembeli TikTok Seller
(`seller-id.tokopedia.com`) yang pesanannya belum dibayar, untuk beberapa toko sekaligus.
Pengiriman dilakukan lewat Chrome asli (DrissionPage), dengan pengaman berlapis agar pembeli
tidak menerima pesan yang sama dua kali.

## Mulai cepat

1. Klik dua kali `instalasi.bat` (sekali saja).
2. Klik dua kali `follow_up_pembayaran.bat`. Browser terbuka ke <http://127.0.0.1:8765>.
3. Toko yang belum login: klik **Login** pada kartu toko, login di jendela Chrome yang terbuka.
4. Centang toko, pilih inisial, periksa template, lalu klik **Kirim sekarang**.

> **Perhatian:** tombol Kirim mengirim pesan **sungguhan** ke pembeli. Uji dulu satu pesanan
> lewat baris perintah, lihat [docs/cli.md](docs/cli.md).

## Dokumentasi

| Dokumen | Isi |
|---|---|
| [docs/instalasi.md](docs/instalasi.md) | Prasyarat dan cara memasang |
| [docs/penggunaan.md](docs/penggunaan.md) | Memakai UI web: toko, template, inisial, kirim |
| [docs/login_toko.md](docs/login_toko.md) | Login, login ulang, dan validasi akun |
| [docs/log_pengiriman.md](docs/log_pengiriman.md) | Membaca tab Log dan arti status |
| [docs/pencegahan_pesan_ganda.md](docs/pencegahan_pesan_ganda.md) | Lapisan pengaman kirim ganda dan salah kirim |
| [docs/cli.md](docs/cli.md) | Dry-run dan kirim lewat baris perintah |
| [docs/data_dan_keamanan.md](docs/data_dan_keamanan.md) | Struktur data, berkas rahasia, keamanan lokal |
| [docs/pemecahan_masalah.md](docs/pemecahan_masalah.md) | Masalah umum dan solusinya |

## Struktur singkat

```
src/          kode aplikasi (bot, server web, login)
web/          antarmuka web (satu berkas HTML)
data/         data runtime per toko (diabaikan Git, berisi rahasia)
docs/         dokumentasi
```

## Persyaratan

Windows, Python 3.10+, Google Chrome, dan koneksi internet.
