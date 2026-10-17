# Pencegahan pesan ganda dan salah kirim

Mengirim pesan yang sama dua kali ke pembeli terasa seperti spam, dan salah kirim ke pembeli lain
lebih buruk. Pengamannya berlapis, dan semuanya condong ke **tidak mengirim** bila ragu.

## Lapisan

1. **Log per pesanan.** Pesanan yang sudah ada di `send_log.json` (`mencoba`, `terkirim`,
   `sudah_ada_di_chat`, `tidak_pasti`) tidak diproses lagi.
2. **Kunci per toko.** `run.lock` mencegah dua proses pada toko yang sama. Klik ganda Kirim ditolak.
3. **Identitas percakapan.** Halaman chat bisa sempat menampilkan percakapan lain. Bot hanya
   percaya halaman bila ID pesanan tampil dan header percakapan memuat nama yang cocok dengan
   pembeli pesanan itu (huruf awal, huruf akhir, panjang). Kartu terpilih di daftar, bila ada,
   harus sama.
4. **"Sudah ada" hanya dari gelembung pesan kita** (`.chatd-message--right pre` di dalam daftar
   pesan), bukan dari seluruh halaman. Yang dicocokkan 40 karakter awal pesan.
5. **Riwayat harus lengkap.** Teks halaman stabil dan penanda "Tidak ada pesan sebelumnya" tampil,
   kecuali pesan kita sudah ketemu.
6. **Cek ulang sebelum mengetik.** Halaman yang berpindah di tengah proses membatalkan pengiriman.
7. **Catat sebelum mengetik.** Status `mencoba` ditulis setelah kotak input terbukti bisa diklik
   dan tepat sebelum mengetik, jadi crash setelah Enter pun tidak mengulang pengiriman.
8. **Berhenti saat tidak pasti.** Enter ditekan tetapi pesan tidak terverifikasi: toko berhenti dan
   pesanan tidak dikirim ulang.

## Bila ragu, bot tidak mengirim

Hasil `belum_ketik` (tidak dicatat, dicoba lagi pada run berikutnya) muncul bila:

- kotak input tidak ditemukan atau tidak bisa diklik;
- ID pesanan atau header pembeli tidak cocok setelah menunggu 20 detik;
- daftar pesan tidak ditemukan;
- riwayat tidak stabil atau belum lengkap.

## Batas yang perlu diketahui

- Dua pembeli berbeda dengan huruf awal, huruf akhir, dan panjang nama yang sama bisa lolos
  pencocokan nama. Risikonya kecil dan dilapisi pengecekan lain, tetapi tidak nol.
- Mengubah kalimat awal template membuat pesan lama tidak dikenali.
- Pesanan tanpa nama pembeli (`?`) tidak bisa diverifikasi dan tidak dikirim.
- Menghapus `send_log.json` melepas lapisan 1; lapisan 3-5 tetap melindungi.

Kode: `src/chat.py` dan `src/runner.py`.
