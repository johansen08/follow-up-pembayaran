# Log pengiriman

Tab **Log pengiriman** muncul otomatis saat Anda menekan Kirim, dan menampilkan riwayat dari
`data/stores/<toko>/send_log.json`.

## Bagian layar

- **Banner**: toko dan nomor pesanan yang sedang diproses, atau ringkasan setelah selesai.
- **Per toko**: kartu dengan status toko, progres, dan hitungan. Klik kartu untuk memfilter tabel.
- **Daftar pesanan**: tabel dengan filter toko, filter status, dan pencarian nomor pesanan.

## Status

Status pesanan (baris tabel):

| Status | Arti |
|---|---|
| **Terkirim** | Pesan terbukti muncul di percakapan |
| **Perlu dicek** | Pesanan sudah diproses tetapi pengiriman gagal atau tidak terverifikasi. Cek chat pesanan itu manual |
| *Memproses* | Penanda sementara pada pesanan yang sedang berjalan |

Status toko (kartu): **Berjalan**, **Selesai**, **Berhenti**. Berhenti disertai alasannya, misalnya
"Dihentikan pengguna" atau "Cek chat pesanan ... secara manual".

Pesanan yang dilewati program (pesan sudah ada di chat atau tanpa link chat) **tidak ditampilkan**.
Jumlahnya terlihat pada ikon **i** di kartu toko.

## Kolom Masuk

Waktu pesanan pertama kali dicatat program. Umur **2 hari atau lebih** berwarna oranye sebagai
penanda mendekati batas pembayaran. Ubah batasnya lewat `BATAS_HARI` di `web/index.html`.
Klik judul kolom untuk membalik urutan (terbaru atau terlama).

## Perlu dicek

Toko berhenti saat menemui status ini agar tidak terjadi pengiriman ganda. Pesanannya **tidak**
dikirim ulang otomatis. Buka chat pesanan itu dan periksa apakah pesan sampai.

Untuk membuka kunci suatu pesanan setelah Anda memastikan pesannya belum terkirim, hapus entrinya
dari `send_log.json` (buat cadangan berkas dulu).

## Privasi

Nama pembeli tidak pernah dikirim ke UI maupun ditampilkan di log. Tombol **Salin no. pesanan**
menyalin nomor sesuai filter yang aktif.
