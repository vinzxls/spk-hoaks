"""Pemeriksa database SPK — dipakai saat login gagal di laptop baru.

Skrip ini HANYA MEMBACA, tidak mengubah apa pun. Hasilnya dipakai untuk
mengetahui bagian mana yang bermasalah: konfigurasi koneksi, database
yang belum dibuat, tabel yang belum ada, atau akun admin yang belum
terisi oleh db/seed.sql.

Jalankan lewat "Cek Database.bat", atau:

    .venv\\Scripts\\python.exe cek_database.py
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import config  # noqa: E402

TABEL_WAJIB = (
    "admin",
    "mahasiswa",
    "kriteria",
    "subkriteria",
    "jawaban_kuesioner",
    "bobot_fahp",
    "hasil_penilaian",
    "matriks_perbandingan",
)

masalah: list[str] = []


def judul(teks: str) -> None:
    print()
    print("=" * 62)
    print(teks)
    print("=" * 62)


def utama() -> int:
    judul("PEMERIKSAAN DATABASE SPK RISIKO HOAKS")

    db = config.DB_CONFIG
    sandi = str(db.get("password") or "")
    print("[1] Konfigurasi di config.py")
    print(f"    host     : {db.get('host')}")
    print(f"    port     : {db.get('port')}")
    print(f"    user     : {db.get('user')}")
    print(f"    password : {'(kosong)' if not sandi else '(terisi)'}")
    print(f"    database : {db.get('database')}")

    print()
    print("[2] Menghubungi MySQL ...")
    try:
        import pymysql
    except ModuleNotFoundError:
        print("    GAGAL: pymysql belum terpasang.")
        print("    Jalankan: .venv\\Scripts\\pip install -r requirements.txt")
        masalah.append("pymysql belum terpasang (venv belum dibuat / pip gagal)")
        return 1

    try:
        koneksi = pymysql.connect(
            host=str(db["host"]),
            port=int(db["port"]),
            user=str(db["user"]),
            password=sandi,
            database=str(db["database"]),
            charset=str(db["charset"]),
        )
    except Exception as exc:
        kode = exc.args[0] if exc.args else None
        print(f"    GAGAL: {type(exc).__name__} (kode {kode})")
        print(f"    pesan: {exc}")
        print()
        if kode == 2003:
            print("    Artinya: MySQL tidak menyala atau port salah.")
            print("    Perbaikan: buka Laragon, klik Start All, tunggu hijau.")
            masalah.append("MySQL tidak bisa dihubungi (kode 2003)")
        elif kode == 1045:
            print("    Artinya: user/password MySQL ditolak.")
            print("    Perbaikan: sesuaikan 'user' dan 'password' di config.py.")
            masalah.append("user/password MySQL ditolak (kode 1045)")
        elif kode == 1049:
            print("    Artinya: database belum dibuat.")
            print("    Perbaikan: klik dua kali 'Impor Database.bat'.")
            masalah.append("database belum ada (kode 1049)")
        elif kode == 1044:
            print("    Artinya: user MySQL tidak punya akses ke database itu.")
            masalah.append("akses database ditolak (kode 1044)")
        else:
            masalah.append(f"gagal terhubung ke MySQL: {exc}")
        return 1

    print("    OK, tersambung.")

    with koneksi.cursor() as cur:
        cur.execute("SELECT DATABASE() AS db, VERSION() AS versi")
        info = cur.fetchone()
        print(f"    database aktif : {info[0]}")
        print(f"    versi MySQL    : {info[1]}")

        print()
        print("[3] Tabel yang ada")
        cur.execute("SHOW TABLES")
        ada = {r[0] for r in cur.fetchall()}
        for nama in TABEL_WAJIB:
            print(f"    {'OK  ' if nama in ada else 'HILANG'}  {nama}")
        hilang = [t for t in TABEL_WAJIB if t not in ada]
        if hilang:
            print()
            print("    Ada tabel yang belum dibuat. Jalankan 'Impor Database.bat'.")
            masalah.append("tabel belum lengkap: " + ", ".join(hilang))
            return 1

        print()
        print("[4] Isi data")
        jumlah: dict[str, int] = {}
        for nama in TABEL_WAJIB:
            cur.execute(f"SELECT COUNT(*) FROM {nama}")
            jumlah[nama] = int(cur.fetchone()[0])
            print(f"    {nama:22s}: {jumlah[nama]} baris")

        print()
        print("[5] Akun admin")
        cur.execute("SELECT username, password FROM admin ORDER BY username")
        admin_rows = cur.fetchall()
        if not admin_rows:
            print("    KOSONG: belum ada akun admin sama sekali.")
            print("    Inilah penyebab login admin gagal.")
            print("    Perbaikan: jalankan 'Impor Database.bat' (data awal mengisi admin).")
            masalah.append("tabel admin kosong")
        for username, hash_tersimpan in admin_rows:
            cocok = hashlib.sha256(
                f"{username}admin123".encode("utf-8")
            ).hexdigest() == str(hash_tersimpan)
            print(
                f"    {username:15s} "
                f"{'password admin123 COCOK' if cocok else 'password admin123 TIDAK cocok'}"
            )
            if not cocok:
                masalah.append(f"hash admin '{username}' bukan untuk admin123")

        print()
        print("[6] Akun mahasiswa (perlu dibuat admin lewat menu Kelola Mahasiswa)")
        cur.execute("SELECT username, nama FROM mahasiswa ORDER BY username")
        mhs_rows = cur.fetchall()
        if not mhs_rows:
            print("    belum ada akun mahasiswa.")
            print("    Ini NORMAL di laptop baru: login mahasiswa memang belum bisa.")
        for username, nama in mhs_rows:
            print(f"    {username}  ({nama})")

    koneksi.close()

    judul("KESIMPULAN")
    if not masalah:
        print("Database sehat. Kalau login masih gagal, periksa:")
        print("  - Toggle peran (Admin/Mahasiswa) harus sesuai akun.")
        print("  - Password diketik tanpa spasi di depan/belakang.")
        print("  - Caps Lock mati, dan huruf besar/kecil berpengaruh.")
        return 0

    print("Ditemukan masalah:")
    for i, m in enumerate(masalah, 1):
        print(f"  {i}. {m}")
    print()
    print("Kirimkan seluruh hasil di layar ini untuk ditindaklanjuti.")
    return 1


if __name__ == "__main__":
    try:
        sys.exit(utama())
    except Exception as exc:  # pragma: no cover - jalur darurat
        print()
        print(f"Pemeriksaan berhenti karena error tak terduga: {exc!r}")
        sys.exit(1)
