# Dayynime Portfolio

Website portofolio dan daftar harga jasa pembuatan website/aplikasi anime (Flask).

## Jalankan lokal (Termux / PC)

```bash
pip install -r requirements.txt
export WHATSAPP_NUMBER=6285199329163   # opsional, defaultnya sudah nomor ini
python app.py
```

Buka http://127.0.0.1:5000

## Ubah isi

Semua teks, harga, fitur paket, dan karya ada di bagian DATA di `app.py`.
Harga dipisah per jenis produk (Website dan Aplikasi Android) di `CATEGORIES`. Kalau `price` diisi `None`, kartu menampilkan "Hubungi untuk harga".
Ganti `static/img/zenime-profile.jpg` kalau mau screenshot lain.

## Deploy ke Vercel

1. Upload folder ini ke GitHub (repo baru, isi folder ini langsung di root repo).
2. Di Vercel: Add New > Project > import repo itu. Framework Preset biarkan "Other". Tidak perlu mengubah Build Command atau Output Directory.
3. Di Settings > Environment Variables, tambahkan `WHATSAPP_NUMBER` (format 6281234567890, tanpa + atau spasi). Kalau dikosongkan, dipakai nomor bawaan di `app.py`.
4. Deploy. Setiap `git push` ke branch utama otomatis deploy ulang.

Lewat CLI: `npm i -g vercel`, lalu jalankan `vercel` (preview) atau `vercel --prod` dari folder ini.

Catatan: `vercel.json` memakai `includeFiles` supaya folder `templates/` dan `static/` ikut terbawa ke fungsi Python. Gambar bukti transaksi di `static/img/bukti/` ikut terbawa juga, jadi setelah menambah gambar cukup push ke GitHub.

## Halaman

| Alamat | Isi |
| --- | --- |
| `/` | Beranda ringkas: hero, layanan, harga mulai dari, karya unggulan |
| `/layanan` | Penjelasan tiap layanan |
| `/harga` | Paket per jenis produk plus tabel perbandingan (`/harga?jenis=app` membuka tab aplikasi) |
| `/karya`, `/karya/zenime` | Daftar karya dan halaman detail |
| `/katalog`, `/katalog/<slug>` | Produk jadi (list + detail), status tersedia/terjual |
| `/admin` | Admin produk jadi (login password), tidak ada di menu |
| `/pesan` | Form pemesanan. Hasilnya dikirim ke `/pesan/kirim`, lalu diarahkan ke WhatsApp dengan pesan terisi |
| `/syarat` | Syarat dan ketentuan |
| `/alur-faq` | Alur pemesanan dan FAQ |
| `/tentang` | Tentang developer |
| `/testimoni` | Muncul di menu hanya kalau sudah ada isinya |
| 404 | Halaman error |

## Ubah isi

- Teks, harga, paket, FAQ, syarat, tentang: bagian DATA di `app.py`.
- Testimoni: isi `TESTIMONIALS` di `app.py`, dan/atau taruh gambar bukti transaksi di `static/img/bukti/` (samarkan nama dan nomor pelanggan dulu).
- Detail karya baru: tambah item di `PROJECTS` (beri `slug`) dan `PROJECT_DETAILS`.
- Fitur tambahan di form pemesanan: `FEATURE_OPTIONS`.

## Struktur tampilan

- `templates/base.html`: kerangka (navbar, footer, tombol WhatsApp). Halaman lain memakai `{% extends "base.html" %}`.
- `templates/_macros.html`: tombol dan ikon yang dipakai ulang.
- `static/css/style.css`: semua gaya. Warna ada di `:root` paling atas (diambil dari aplikasi Zenime).
- `static/js/main.js`: navbar, menu mobile, animasi muncul saat scroll, efek sorot kursor, ringkasan form pemesanan.
- Animasi otomatis mati kalau perangkat memakai pengaturan "kurangi gerakan".

## Produk jadi (admin + Supabase + Cloudinary)

Produk jadi (aplikasi/website) dikelola dari `/admin`: judul, deskripsi, harga normal, harga diskon,
foto sebanyak apa pun (disimpan di Cloudinary), status tersedia/terjual, dan catatan pembeli (hanya admin).
Halaman publik `/katalog` menampilkan list dengan thumbnail, klik masuk ke detail produk.

### Setup sekali saja

1. **Supabase**: buka SQL Editor, jalankan isi `supabase_schema.sql`.
2. **Cloudinary**: ambil Cloud name, API key, dan API secret dari dashboard.
3. **Environment variable** (Vercel > Settings > Environment Variables, atau `export` di Termux):

| Nama | Isi |
| --- | --- |
| `SUPABASE_URL` | URL project, contoh `https://xxxx.supabase.co` |
| `SUPABASE_SERVICE_KEY` | `service_role` key (rahasia, jangan dipakai di frontend) |
| `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET` | Dari dashboard Cloudinary |
| `ADMIN_PASSWORD` | Password login `/admin`, pakai yang panjang |
| `SECRET_KEY` | Opsional. String acak untuk tanda tangan sesi (kalau kosong diturunkan dari `ADMIN_PASSWORD`) |

4. Deploy ulang, buka `/admin/login`.

### Catatan

- Foto diunggah langsung dari browser ke Cloudinary (API secret tetap di server). Foto pertama jadi sampul.
- Status terjual di halaman publik bisa tertunda sampai sekitar 1 menit karena cache di edge Vercel.
- Menghapus produk tidak menghapus fotonya di Cloudinary.
- Teks langkah beli dan pindah kepemilikan ada di `TRANSFER_STEPS` di `app.py`.
