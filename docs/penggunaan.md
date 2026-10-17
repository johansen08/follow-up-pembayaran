# Penggunaan UI web

Jalankan `follow_up_pembayaran.bat`. Browser terbuka ke <http://127.0.0.1:8765>.
Menutup jendela hitam `.bat` menghentikan server.

## Tab Toko

Pertama kali, daftar toko kosong: klik **＋ Tambah toko**, isi nama toko, lalu klik **Login** pada kartunya.

- **Kartu toko** menampilkan status **Siap** (cookies ada) atau **Belum login**, serta
  cuplikan pesan yang akan dikirim.
- **Centang** kartu untuk memilih toko yang dijalankan. Toko Belum login tidak bisa dicentang.
  Tombol *Pilih semua siap* dan *Kosongkan* tersedia di atas kartu.
- **＋ Tambah toko** membuat folder data toko baru. Nama toko 2-40 karakter
  (huruf, angka, spasi, `.`, `_`, `-`).

## Inisial

Inisial dipasang di akhir pesan sebagai `~-f` (untuk inisial `f`).

- Klik chip untuk memilih inisial aktif. Chip ✕ menghapus.
- Tambah inisial baru (1-6 huruf atau angka) lewat kolom di bawah chip; langsung terpilih.
- Inisial aktif dipakai oleh seluruh toko pada run berikutnya.

## Template pesan

Klik **✎ Edit template** pada kartu. Panel di kanan berisi editor dan pratinjau.

- Variabel yang tersedia: `{toko}` dan `{inisial}`. Variabel lain **ditolak** karena akan
  terkirim apa adanya ke pembeli.
- Maksimal 1500 karakter, tidak boleh kosong.
- Perubahan tersimpan otomatis. *Terapkan ke semua toko* menyalin pesan itu ke semua toko.
- Template bawaan: pengingat pembayaran sebelum jam 12:00 yang berakhir `~-{inisial}`.

> Pengecekan "pesan sudah ada" mencocokkan 40 karakter awal pesan. Kalau Anda mengubah
> kalimat awal template, pesan lama tidak lagi dikenali. Lihat
> [pencegahan_pesan_ganda.md](pencegahan_pesan_ganda.md).

## Menjalankan

1. Centang toko, pastikan inisial benar.
2. Klik **Kirim sekarang**, lalu konfirmasi pada dialog.
3. Tampilan pindah ke tab **Log pengiriman** (lihat [log_pengiriman.md](log_pengiriman.md)).

Toko diproses satu per satu, dengan jeda acak 8-20 detik setelah tiap pesan terkirim.
**Hentikan** berhenti setelah pesanan yang sedang diproses selesai.

UI tidak punya mode dry-run dan tidak punya batas jumlah pesan per toko. Untuk uji kecil
gunakan [cli.md](cli.md).
