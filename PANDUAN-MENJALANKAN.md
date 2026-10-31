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

## B2. Memasang di Laptop Baru (Menarik dari GitHub)

Bagian ini dipakai **sekali saja** saat aplikasi dipasang di laptop lain.
Kode proyek tersimpan di: **https://github.com/vinzxls/spk-hoaks**

### Langkah 1 — Pasang prasyarat

1. **Git** — unduh dari https://git-scm.com/download/win, install dengan
   pilihan bawaan (semua *Next*).
2. **Python 3.13** — unduh dari https://www.python.org/downloads/
   Saat instalasi, **centang "Add python.exe to PATH"**.
3. **Laragon** — seperti biasa, untuk MySQL.

Pastikan ketiganya sudah terpasang sebelum lanjut.

### Langkah 2 — Unduh kode dari GitHub

Buka **Command Prompt** (`Win + R`, ketik `cmd`, Enter), lalu jalankan:

```cmd
cd C:\
git clone https://github.com/vinzxls/spk-hoaks.git "Orderan Sela\spk_hoaks"
cd "Orderan Sela\spk_hoaks"
```

Perintah ini membuat folder `C:\Orderan Sela\spk_hoaks` berisi seluruh kode.
Kalau repo GitHub-nya nanti diperbarui, cukup jalankan `git pull` di folder itu.

### Langkah 3 — Buat lingkungan Python

Masih di Command Prompt yang sama:

```cmd
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

Tunggu sampai selesai. Proses ini mengunduh pymysql, reportlab, openpyxl,
dan pytest.

### Langkah 4 — Nyalakan MySQL lalu impor database

1. Buka **Laragon** → klik **Start All** → tunggu MySQL berwarna hijau.
2. Di folder `C:\Orderan Sela\spk_hoaks`, klik dua kali
   **`Impor Database.bat`**.
3. Skrip itu membuat database `spk_hoaks`, seluruh tabel, dan mengisi data
   awal (admin, 6 kriteria, 30 subkriteria, matriks perbandingan).
4. Tunggu sampai muncul tulisan **SELESAI**.

> Skrip ini **menolak berjalan** kalau database sudah berisi jawaban
> kuesioner, supaya data asli tidak terhapus. Kalau ingin mulai dari nol,
> hapus dulu database `spk_hoaks` lewat Laragon, lalu jalankan lagi.

### Langkah 5 — Jalankan aplikasi

Klik dua kali **`Jalankan Aplikasi.bat`**, lalu login:

| Peran | Username | Password |
|---|---|---|
| Admin | `admin` | `admin123` |

Selesai. Langkah 1–4 tidak perlu diulang lagi di kemudian hari — cukup
bagian **A** di atas.

### Kalau langkahnya ingin lebih singkat

Semua perintah Langkah 2–3 bisa digabung jadi satu blok:

```cmd
cd C:\
git clone https://github.com/vinzxls/spk-hoaks.git "Orderan Sela\spk_hoaks"
cd "Orderan Sela\spk_hoaks"
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

---

## C. Syarat Sistem (Sudah Disiapkan, untuk Referensi)

| Komponen | Keterangan |
|---|---|
| Python | Versi 3.13 |
| MySQL | Lewat Laragon (port 3306, user `root`, tanpa password) |
| Database | Nama database: `spk_hoaks` |
| Library Python | Sesuai `requirements.txt` (pymysql, reportlab, openpyxl, pytest) |
| Sumber kode | https://github.com/vinzxls/spk-hoaks |

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
Folder `.venv` tidak ikut tersimpan di GitHub (ukurannya besar dan khusus
perangkat). Buat ulang:

```cmd
cd "C:\Orderan Sela\spk_hoaks"
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

### 4b. Pesan "python is not recognized" padahal Python sudah dipasang
Python belum masuk PATH. Cara tercepat: pasang ulang Python 3.13, pilih
**Modify**, dan centang **"Add Python to environment variables"**. Atau
pakai perintah `py` sebagai ganti `python`:

```cmd
py -m venv .venv
```

### 5. Aplikasi berjalan tapi data kosong
Jalankan **`Impor Database.bat`** (MySQL harus menyala). Atau lewat terminal:

```cmd
mysql -u root < db\schema.sql
mysql -u root spk_hoaks < db\seed.sql
```

### 6. Database sudah berisi data lama dan ingin mulai dari nol
1. Buka **Laragon** → **Database** (atau HeidiSQL).
2. Hapus database `spk_hoaks`.
3. Klik dua kali **`Impor Database.bat`** lagi.

> Menghapus database ikut menghapus semua akun mahasiswa dan jawaban
> kuesioner. Ekspor dulu rekapnya lewat menu **Kuesioner → Ekspor Excel**
> kalau datanya masih dibutuhkan.

---

## E. Ringkasan Cepat

**Setiap mau pakai aplikasi:**
1. Laragon → **Start All**
2. Klik dua kali **`Jalankan Aplikasi.bat`**
3. Login sebagai `admin` / `admin123`

**Selesai pakai:**
1. Tutup aplikasi
2. Laragon → **Stop All**
