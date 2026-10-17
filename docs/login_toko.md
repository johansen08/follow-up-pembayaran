# Login toko

Bot memakai cookies login TikTok Seller yang disimpan per toko. Login dilakukan manual di
Chrome (termasuk captcha dan OTP); cookies diambil otomatis setelahnya.

## Kapan perlu

- Toko berstatus **Belum login**: tombol **Login** pada kartu.
- Sesi toko kedaluwarsa (run gagal dengan pesan error): tombol **⟳ Login ulang** pada kartu toko Siap.

## Alur

1. Klik **Login** atau **Login ulang**. Chrome terbuka ke TikTok Seller memakai profil toko itu
   (`data/stores/<toko>/chrome-profile`).
2. Login di jendela itu. Jangan ditutup.
3. Setelah cookie autentikasi (`SELLER_TOKEN` dan `sessionid`) muncul, bot memeriksa akun:
   mengambil daftar pesanan dan mencocokkan `seller_id` dengan folder toko.
4. Bila cocok, cookies disimpan ke `data/stores/<toko>/cookies.json`, Chrome ditutup, dan
   kartu berubah menjadi **Siap**.

## Pengaman

- Akun salah (milik toko lain) **ditolak** dan cookies lama **tidak ditimpa**.
- Satu login pada satu waktu. Login ditolak saat proses kirim berjalan, dan kirim ditolak
  saat login berlangsung (keduanya memakai port Chrome bot yang sama).
- Batas waktu 10 menit. Tombol **Batalkan login** menutup Chrome.
- Esc atau klik di luar dialog hanya menyembunyikannya; login tetap berjalan.

## Bila gagal

| Pesan | Arti |
|---|---|
| Login X sedang berlangsung | Selesaikan atau batalkan login yang aktif |
| Proses kirim sedang berjalan | Tunggu run selesai |
| Browser bot lain sedang berjalan (port dipakai) | Tutup Chrome bot yang tersisa |
| ...ternyata milik toko 'Y' | Anda login ke akun toko lain |
| Waktu login habis (10 menit) | Ulangi login |

Lihat juga [pemecahan_masalah.md](pemecahan_masalah.md).
