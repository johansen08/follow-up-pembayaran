# Pemecahan masalah

| Gejala | Penyebab | Solusi |
|---|---|---|
| `run.lock ada: program lain sedang jalan` | Ada proses lain pada toko itu, atau program mati paksa | Pastikan tidak ada proses jalan, lalu hapus `data/stores/<toko>/run.lock` |
| Kartu toko Berhenti: "Kotak chat belum tampil/tidak bisa diklik" | Layout halaman belum siap saat bot mengklik | Jalankan lagi; pesanan tidak terkunci karena log ditulis setelah klik berhasil |
| Berhenti: "Kotak chat tidak ditemukan/tidak bisa diklik" pada pesanan pertama | Halaman lambat atau selector berubah | Coba lagi; bila terus terjadi, tampilan TikTok mungkin berubah dan aplikasi perlu diperbarui |
| Output: "percakapan yang tampil bukan milik pembeli ..." | Halaman masih menampilkan percakapan lain; bot sengaja tidak mengirim | Tidak perlu tindakan; dicoba lagi pada run berikutnya |
| Output: "riwayat lama belum termuat penuh" | Riwayat chat panjang | Kirim manual untuk pesanan itu atau abaikan |
| Pesanan berstatus **Perlu dicek** | Pengiriman tidak terverifikasi | Cek chat pesanan itu manual. Lihat [log_pengiriman.md](log_pengiriman.md) |
| "request order/list tidak tertangkap - cek login/cookies" | Cookies kedaluwarsa | Klik **⟳ Login ulang** pada kartu toko |
| "seller_id ... ternyata milik toko ..." | Cookies atau login ke akun toko lain | Login ulang dengan akun yang benar; hapus `store.json` hanya bila memang disengaja |
| Login ditolak: "port dipakai" | Chrome bot lain masih berjalan | Tutup jendela Chrome bot yang tersisa |
| Server gagal dibuka karena port 8765 sudah dipakai | Server web yang lama masih berjalan | Tutup jendela `.bat` yang lama |
| UI tidak mengikuti perubahan kode Python | Server lama masih berjalan | Tutup jendela `.bat`, jalankan lagi |
| `Python 3 tidak ditemukan di PATH` | Python belum terpasang atau tidak di `PATH` | Pasang Python 3.10+ dan centang "Add to PATH" |
| `PermissionError` pada `send_log.json` | Berkas sedang dibaca saat diganti (Windows) | Sudah ditangani dengan percobaan ulang otomatis |

## Pop-up peringatan + suara

Saat proses terhenti (captcha, sesi habis, pengiriman tidak terverifikasi, error lain), muncul pop-up
di pojok kanan bawah layar disertai bunyi alarm. Pop-up selalu di atas jendela Chrome dan **menutup
sendiri setelah 10 detik** (atau klik **Tutup**). Pesan yang sama tetap tampil di kartu toko.

- **Captcha**: dipantau tiap 5 detik di semua tab Chrome bot. Pop-up muncul sekali per kemunculan.
  Geser captcha di jendela Chrome; bila proses sudah berhenti, jalankan ulang.
- Berhenti karena tombol **Hentikan** tidak memunculkan pop-up.
- Kode: `src/notif.py` (pop-up + suara, tkinter + winsound), `src/captcha.py` (pemantau).

Folder `data/stores/<toko>/chrome-profile` bisa dihapus untuk mereset profil Chrome toko; lakukan
Login ulang setelahnya.

## Log berkas

Semua kejadian dan error tersimpan otomatis di `data/log/`, tidak perlu menyalin dari konsol:

| Berkas | Isi |
|---|---|
| `error.log` | Hanya peringatan dan error, lengkap dengan traceback. **Buka ini dulu.** |
| `fu-<tanggal>.log` | Seluruh output program per hari, tiap baris berstempel waktu. Berkas lebih dari 14 hari dihapus otomatis |

Yang tercatat: toko berhenti (beserta alasannya), error saat cek/kirim chat per percobaan, gagal ambil
daftar pesanan, login gagal, error server web, error pemantau captcha/pop-up, dan error tak
tertangani di thread mana pun. Kode: `src/logs.py`.
