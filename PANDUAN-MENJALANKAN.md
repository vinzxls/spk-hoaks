# Panduan Menjalankan Aplikasi
## SPK Penilaian Tingkat Risiko Penyebaran Hoaks

Panduan ini untuk **Sela** agar bisa menjalankan sistem secara mandiri.
Lokasi proyek di laptop: `C:\Orderan Sela\spk_hoaks`

---

## A. Cara Menjalankan (Rutin, Sehari-hari)

### Langkah 1 — Nyalakan MySQL
1. Buka **Laragon**.
2. Klik **Start All** (atau pastikan tulisan **MySQL** sudah berwarna hijau/berjalan).
3. Tunggu sampai MySQL benar-benar aktif sebelum lanjut.

> Aplikasi **tidak akan jalan** kalau MySQL belum menyala.

### Langkah 2 — Jalankan Aplikasi
1. Buka folder `C:\Orderan Sela\spk_hoaks`.
2. Klik dua kali file **`Jalankan Aplikasi.bat`**.
3. Jendela hitam akan muncul, lalu aplikasi (jendela login) terbuka.
4. **Jangan tutup jendela hitam** selama aplikasi dipakai.

### Langkah 3 — Login
Klik tombol **Login** setelah mengisi akun:

| Peran | Username | Password |
|---|---|---|
| Admin | `admin` | `admin123` |
| Mahasiswa | (lihat catatan di bawah) | (lihat catatan di bawah) |

> **Catatan mahasiswa:** akun mahasiswa dibuat oleh Admin melalui menu
> **Kelola Mahasiswa** di dalam aplikasi. Password dibuat di situ.

### Langkah 4 — Menutup Aplikasi
1. Tutup jendela aplikasi seperti biasa (tombol X).
2. Tutup jendela hitam (kalau masih terbuka).
3. Di Laragon, klik **Stop All** untuk mematikan MySQL.

---

## B. Cara Alternatif (lewat Terminal)

Kalau file `.bat` tidak bisa dipakai:

```cmd
cd "C:\Orderan Sela\spk_hoaks"
.venv\Scripts\activate
python main.py
```

---

## C. Syarat Sistem (Sudah Disiapkan, untuk Referensi)

| Komponen | Keterangan |
|---|---|
| Python | Versi 3.13 |
| MySQL | Lewat Laragon (port 3306, user `root`, tanpa password) |
| Database | Nama database: `spk_hoaks` |
| Library Python | Sesuai `requirements.txt` (pymysql, reportlab, pytest) |

---

## D. Kalau Ada Masalah

### 1. Tidak bisa login / "Username atau password salah"
Password disimpan dalam bentuk **hash** (SHA256), bukan teks biasa.
Untuk mereset password admin, buka terminal MySQL:

```sql
USE spk_hoaks;
UPDATE admin SET password = SHA2(CONCAT('admin','admin123'), 256) WHERE username = 'admin';
```

### 1b. Mahasiswa tidak bisa login setelah username-nya diubah
Password disimpan memakai pola **hash(username + password)**. Jadi kalau
username mahasiswa diubah tanpa mengisi password baru, password lamanya tidak
lagi cocok dan akun itu tidak bisa dipakai login.

Aplikasi sekarang **menolak** perubahan username yang tidak disertai password
baru. Kalau sudah terlanjur terjadi, buka menu **Kelola Mahasiswa** → pilih
mahasiswa → **Edit** → isi password baru → **Simpan**. Setelah itu login pakai
username baru + password baru tadi.

### 2. Pesan "Tidak dapat terhubung ke database MySQL"
- Pastikan **MySQL di Laragon sudah Start**.
- Pastikan nama database sudah benar: `spk_hoaks`.
- Cek file `config.py`, bagian `DB_CONFIG`.

### 3. Pesan "python is not recognized"
- Python belum terpasang atau belum masuk PATH. Pasang ulang Python 3.13
  dan centang **"Add Python to PATH"** saat instalasi.

### 4. Pesan "Virtual environment .venv tidak ditemukan"
Buat ulang lingkungan virtual:

```cmd
cd "C:\Orderan Sela\spk_hoaks"
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

### 5. Aplikasi berjalan tapi data kosong
Impor ulang data awal (aman dijalankan berulang):

```cmd
mysql -u root spk_hoaks < db/seed.sql
```

---

## E. Ringkasan Cepat

**Setiap mau pakai aplikasi:**
1. Laragon → **Start All**
2. Klik dua kali **`Jalankan Aplikasi.bat`**
3. Login sebagai `admin` / `admin123`

**Selesai pakai:**
1. Tutup aplikasi
2. Laragon → **Stop All**
