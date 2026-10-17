# Baris perintah

```bash
python main.py [--toko NAMA] [--kirim] [--limit N] [--pesan TEKS]
```

| Opsi | Arti |
|---|---|
| `--toko NAMA` | Nama toko, boleh diulang. Bawaan: semua toko yang punya `cookies.json` |
| `--kirim` | Benar-benar mengirim. **Tanpa opsi ini adalah dry-run** |
| `--limit N` | Maksimal N pesanan per toko (0 = semua) |
| `--pesan TEKS` | Ganti teks pesan (bawaan: `PESAN_DEFAULT` di `src/config.py`, berakhir `~-f`) |

## Dry-run (aman)

```bash
python main.py --toko "NAMA TOKO" --limit 3
```

Dry-run membuka Chrome, mengambil daftar pesanan belum bayar, lalu **membuka chat tiap pesanan** dan
memutuskan. Tidak mengetik, tidak menekan Enter, tidak menulis log.

```
[1/3] 586...: PERLU KIRIM (pesan belum ada di chat)
[2/3] 586...: TIDAK PERLU KIRIM (pesan yang sama sudah ada di chat)
[3/3] 586...: TIDAK BISA DICEK (kotak input chat tidak ditemukan)
```

`TIDAK BISA DICEK` juga muncul bila percakapan atau riwayat tidak terverifikasi
(lihat [pencegahan_pesan_ganda.md](pencegahan_pesan_ganda.md)).

## Kirim sungguhan

```bash
python main.py --toko "NAMA TOKO" --limit 1 --kirim
```

Mengirim pesan nyata ke pembeli. Mulailah dari `--limit 1`, lalu cek chat pembelinya manual.
Jalankan perintah yang sama sekali lagi: pesanan tadi harus tidak diproses lagi.

## Catatan

- Nama pembeli tercetak di konsol oleh program. Samarkan bila Anda membagikan keluarannya.
- CLI dan UI web memakai kunci yang sama; keduanya tidak bisa menjalankan toko yang sama bersamaan.
- Template per toko di UI tidak dipakai CLI; CLI memakai `--pesan` atau `PESAN_DEFAULT`.
