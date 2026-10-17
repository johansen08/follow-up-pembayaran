# Data dan keamanan

## Struktur data

```
data/
  app.json                      daftar inisial dan inisial aktif
  stores/<nama-toko>/
    cookies.json                cookies login (RAHASIA)
    send_log.json               log pengiriman per pesanan
    store.json                  seller_id toko (pengikat akun)
    meta.json                   nama dan template pesan toko
    run.lock                    ada selama toko sedang diproses
    chrome-profile/             profil Chrome toko
```

`<nama-toko>` berbentuk kebab-case, misalnya `toko-saya`.

## Berkas rahasia

`cookies.json`, `chrome-profile/`, dan `send_log.json` berisi sesi login dan data pesanan.
Seluruh folder `data/` serta berkas `cookies.json` diabaikan Git. Jangan membagikan isinya.

## Pengikatan akun

Run pertama menyimpan `seller_id` ke `store.json`. Run berikutnya menolak cookies yang `seller_id`-nya
berbeda, atau yang ternyata milik toko lain. Ini mencegah cookies salah folder.

## Keamanan server web

- Server hanya mendengarkan `127.0.0.1`.
- Request yang mengubah data wajib membawa header `X-FU: 1`. Header `Host` dan `Origin` harus lokal,
  sehingga halaman web lain tidak bisa memicu pengiriman.
- Nama pembeli tidak pernah dikirim ke UI.
- Kesalahan server tidak membocorkan stack trace.

## Cadangan

Sebelum mengubah `send_log.json` secara manual, salin berkasnya. Berkas `*.cadangan*` ikut
diabaikan Git.
