"""Authentication: password hashing, credential check, and session state.

Skema hash kata sandi (SEEDED SCHEME - jangan diubah diam-diam):

    SHA256(username + password) sebagai lowercase hex, misalnya::

        hash_password("admin", "admin123")
            == hashlib.sha256(b"adminadmin123").hexdigest()

Skema ini dipilih agar cocok dengan ``db/seed.sql`` yang menyisipkan admin
awal memakai ``SHA2(CONCAT('admin','admin123'), 256)`` milik MySQL.
Alasan kesederhanaan lingkup skripsi: aplikasi desktop lokal satu kampus
dengan MySQL lokal.

PERINGATAN KEAMANAN (keterbatasan yang disadari, bukan kelalaian):
SHA256 tanpa salt per-pengguna dan tanpa key stretching LEMAH terhadap
pembobolan offline (brute-force / rainbow table) bila berkas database
bocor. Skema ini diterima hanya karena model ancaman berupa aplikasi
desktop lokal satu kampus dengan MySQL lokal. JANGAN dipakai untuk
aplikasi production yang terekspos jaringan/internet; di sana gunakan
bcrypt/scrypt/argon2 dengan salt acak per pengguna.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import typing
from dataclasses import dataclass
from typing import Literal

from db.connection import query_one

logger = logging.getLogger(__name__)

Aktor = Literal["admin", "mahasiswa"]


def hash_password(username: str, password: str) -> str:
    """Hitung hash kata sandi sesuai skema seed: SHA256(username + password).

    Mengembalikan lowercase hex 64 karakter. Harus sama persis dengan
    ``SHA2(CONCAT(username, password), 256)`` di MySQL agar admin hasil
    seed tetap bisa login. Lihat peringatan keamanan di docstring modul.
    """
    return hashlib.sha256(f"{username}{password}".encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class UserSession:
    """Data sesi pengguna yang sedang login (immutable)."""

    id_user: int
    username: str
    nama: str
    role: Aktor
    # Hanya untuk mahasiswa; None untuk admin.
    id_mahasiswa: int | None = None
    nim: str | None = None


def authenticate(username: str, password: str, role: Aktor) -> UserSession | None:
    """Verifikasi kredensial dan kembalikan sesi, atau None bila gagal.

    Mencari pengguna di tabel yang sesuai ``role`` lalu membandingkan
    hash memakai ``hmac.compare_digest`` (constant-time).

    Mengembalikan None untuk username salah, kata sandi salah, atau
    baris tanpa hash tersimpan — tanpa memberi tahu penyebabnya agar
    tidak membocorkan username mana yang terdaftar. Upaya gagal
    dicatat di log TANPA kata sandi.

    Raises:
        ValueError: bila ``role`` bukan "admin" maupun "mahasiswa"
            (kesalahan pemrograman, bukan kesalahan pengguna).
    """
    if role != "admin" and role != "mahasiswa":
        raise ValueError(
            f"Peran tidak dikenal: {role!r}. "
            "Peran yang didukung: 'admin', 'mahasiswa'."
        )

    if role == "admin":
        row = query_one(
            "SELECT id_admin, username, password, nama FROM admin WHERE username = %s",
            (username,),
        )
    else:
        row = query_one(
            "SELECT id_mahasiswa, nim, nama, username, password "
            "FROM mahasiswa WHERE username = %s",
            (username,),
        )

    if row is None:
        logger.warning("Login gagal: username tidak ditemukan (peran=%s).", role)
        return None

    stored_hash = str(row["password"])
    candidate = hash_password(username, password)
    if not hmac.compare_digest(candidate, stored_hash):
        logger.warning(
            "Login gagal: kata sandi salah untuk username=%r (peran=%s).",
            username,
            role,
        )
        return None

    if role == "admin":
        return UserSession(
            id_user=int(row["id_admin"]),
            username=str(row["username"]),
            nama=str(row["nama"]),
            role="admin",
        )
    return UserSession(
        id_user=int(row["id_mahasiswa"]),
        username=str(row["username"]),
        nama=str(row["nama"]),
        role="mahasiswa",
        id_mahasiswa=int(row["id_mahasiswa"]),
        nim=str(row["nim"]),
    )


_session: UserSession | None = None


def get_session() -> UserSession | None:
    """Kembalikan sesi aktif, atau None bila belum login."""
    return _session


def set_session(s: UserSession) -> None:
    """Tetapkan sesi aktif (dipanggil setelah login berhasil)."""
    global _session
    _session = s


def clear_session() -> None:
    """Hapus sesi aktif (logout)."""
    global _session
    _session = None


def require_session() -> UserSession:
    """Kembalikan sesi aktif, atau raise bila belum login.

    Raises:
        RuntimeError: bila tidak ada sesi aktif.
    """
    s = get_session()
    if s is None:
        raise RuntimeError("Belum login. Silakan login terlebih dahulu.")
    return s


def require_role(role: Aktor) -> UserSession:
    """Gerbang kontrol akses: pastikan sesi aktif dengan peran yang diminta.

    Dipanggil UI sebelum merender halaman yang dibatasi peran
    (misalnya halaman khusus admin).

    Raises:
        PermissionError: bila belum login atau peran sesi tidak cocok.
    """
    s = get_session()
    if s is None:
        raise PermissionError(
            "Akses ditolak: belum login. Silakan login terlebih dahulu."
        )
    if s.role != role:
        raise PermissionError(
            f"Akses ditolak: halaman ini khusus peran '{role}'."
        )
    return s


def is_logged_in() -> bool:
    """True bila ada sesi aktif."""
    return _session is not None


def maybe_rehash_on_login(
    user: UserSession, table: str, stored_hash: str
) -> bool:
    """Hook migrasi hash saat login pertama (saat ini no-op).

    Tujuan: bila hash tersimpan belum dalam bentuk kanonis skema saat
    ini, hash ulang dan UPDATE barisnya, lalu kembalikan True. Hash
    hasil seed sudah kanonis sehingga fungsi ini normalnya tidak
    melakukan apa-apa dan mengembalikan False.

    Sengaja diimplementasikan sebagai no-op terdokumentasi: tanpa
    penanda skema versi pada baris, tebakan migrasi berisiko merusak
    kredensial, jadi fungsi ini tidak menulis apa pun ke database.
    """
    logger.debug(
        "maybe_rehash_on_login: tidak ada migrasi untuk user=%r tabel=%s.",
        user.username,
        table,
    )
    _ = stored_hash
    return False
