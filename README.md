# SPK Penilaian Tingkat Risiko Penyebaran Hoaks

Aplikasi desktop untuk menilai tingkat risiko penyebaran hoaks pada mahasiswa,
memakai metode **Fuzzy AHP** untuk pembobotan kriteria dan kuesioner Likert 1–5
sebagai instrumen penilaian.

Dibangun dengan **Python 3.13 + Tkinter** (tanpa framework UI eksternal) dan
**MySQL** sebagai basis data.

---

## Fitur

**Sisi Admin**

| Menu | Fungsi |
|---|---|
| Dashboard | Statistik jumlah mahasiswa, pengisi kuesioner, hasil penilaian, dan distribusi kategori risiko |
| Kelola Mahasiswa | Tambah / ubah / hapus akun mahasiswa (NIM, nama, angkatan, username, password) |
| Kuesioner | Lihat jawaban per mahasiswa, ekspor rekap ke Excel format SPSS |
| Kriteria | Kelola 6 kriteria dan 30 subkriteria, serta matriks perbandingan berpasangan |
| Hasil | Hitung nilai risiko tiap mahasiswa, lihat detail skor per kriteria |
| Ranking | Urutan mahasiswa berdasarkan nilai risiko |
| Laporan | Ekspor laporan PDF |

**Sisi Mahasiswa**

| Menu | Fungsi |
|---|---|
| Dashboard | Ringkasan status pengisian dan hasil penilaian |
| Kuesioner | Isi 30 pertanyaan Likert, kirim sekali |

---

## Struktur Proyek

```
spk_hoaks/
├── main.py                  Entry point + routing halaman per peran
├── config.py                Konfigurasi DB, metadata, kategori risiko
├── Jalankan Aplikasi.bat    Peluncur untuk Windows
├── core/
│   ├── auth.py              Hash password, autentikasi, sesi
│   ├── fahp.py              Perhitungan Fuzzy AHP
│   ├── risiko.py            Skoring risiko (murni, tanpa UI/SQL)
│   └── layanan.py           Lapisan layanan: semua query & operasi data
├── db/
│   ├── connection.py        Koneksi MySQL + retry saat koneksi putus
│   ├── schema.sql           Skema tabel
│   └── seed.sql             Data awal (admin, kriteria, subkriteria, matriks)
├── ui/
│   ├── login.py             Halaman login (toggle Admin/Mahasiswa)
│   ├── theme.py             Palet warna & font
│   ├── widgets.py           Komponen bersama (tabel, kartu, donut chart)
│   ├── admin/               7 halaman admin
│   └── mahasiswa/           2 halaman mahasiswa
└── tests/                   Test otomatis (pytest)
```

---

## Cara Menjalankan

### 1. Prasyarat

- Python 3.13
- MySQL 8.x (lewat **Laragon** atau XAMPP), port `3306`, user `root`, tanpa password

### 2. Siapkan database

```bash
mysql -u root -e "CREATE DATABASE IF NOT EXISTS spk_hoaks"
mysql -u root spk_hoaks < db/schema.sql
mysql -u root spk_hoaks < db/seed.sql
```

### 3. Siapkan lingkungan Python

```bash
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

### 4. Jalankan

Klik dua kali **`Jalankan Aplikasi.bat`**, atau lewat terminal:

```bash
.venv\Scripts\python.exe main.py
```

### 5. Login

| Peran | Username | Password |
|---|---|---|
| Admin | `admin` | `admin123` |
| Mahasiswa | dibuat oleh admin lewat menu **Kelola Mahasiswa** | — |

---

## Konfigurasi Database

Sesuaikan di `config.py` bila MySQL Anda memakai password atau port berbeda:

```python
DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "",
    "database": "spk_hoaks",
    "charset": "utf8mb4",
}
```

---

## Metode Perhitungan

**Fuzzy AHP** (`core/fahp.py`)
Matriks perbandingan berpasangan antar kriteria diubah ke Triangular Fuzzy
Number, dihitung sintesis fuzzy, lalu bobot dinormalisasi. Jumlah bobot selalu
1.0.

**Skoring risiko** (`core/risiko.py`)

1. Jawaban subkriteria dikelompokkan per kriteria (dari kode `SKx.y`).
2. Skor kriteria = rata-rata jawaban subkriteria di dalamnya.
3. `R = Σ(w_k × skor_k)` dengan `w_k` bobot Fuzzy AHP.
4. `nilai = (R − 1) / 4 × 100` → skala 0–100.
5. Kategori: **Rendah** (1–40), **Sedang** (41–70), **Tinggi** (71–100).

---

## Test

```bash
.venv\Scripts\python.exe -m pytest -q
```

Test mencakup autentikasi, perhitungan FAHP, skoring risiko (termasuk kasus
batas), routing halaman, serta black-box UI: login, pengisian kuesioner,
ekspor Excel/PDF, dan cascade delete.

> Test black-box butuh MySQL aktif dan database `spk_hoaks` sudah di-seed.
> Tanpa MySQL, test tersebut otomatis di-skip.

---

## Catatan Keamanan

Password disimpan sebagai `SHA256(username + password)` — **tanpa salt dan tanpa
key stretching**. Skema ini dipilih agar cocok dengan seed bawaan dan hanya
diterima karena model ancamannya adalah aplikasi desktop lokal satu kampus
dengan MySQL lokal. **Jangan dipakai untuk aplikasi yang terekspos jaringan.**
Untuk keperluan produksi gunakan bcrypt/scrypt/argon2.

Konsekuensi praktis: mengubah username **wajib** disertai password baru, karena
hash lama terikat pada username lama. Aplikasi menolak perubahan username tanpa
password baru.

---

## Lisensi

Proyek akademik — Program Studi Ilmu Komputer, Universitas Pattimura.
