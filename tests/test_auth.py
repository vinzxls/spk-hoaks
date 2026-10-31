"""Unit test core/auth.py — hash, session lifecycle, access control.

Beberapa tes membutuhkan database dan ditandai skipif MySQL tidak
tersedia.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import sys
import time

import pytest

# ── DB availability helper ──────────────────────────────────

def db_tersedia() -> bool:
    """Coba koneksi ke MySQL dengan timeout singkat."""
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        import pymysql
        c = pymysql.connect(host="localhost", port=3306, user="root", password="",
                            database="spk_hoaks", connect_timeout=2)
        c.close()
        return True
    except Exception:
        return False

SKIP_DB = not db_tersedia()
SKIP_REASON = "MySQL tidak tersedia; tes DB dilewati."


@pytest.fixture(autouse=True, scope="session")
def _clear_session():
    """Pastikan sesi bersih sebelum tes dimulai."""
    from core import auth
    auth.clear_session()
    yield
    auth.clear_session()


# ── Hash password ────────────────────────────────────────────
def test_hash_password_kontrak_seed():
    """Hash admin/admin123 harus sama dengan SHA256('adminadmin123')."""
    from core.auth import hash_password

    expected = hashlib.sha256(b"adminadmin123").hexdigest()
    assert hash_password("admin", "admin123") == expected
    assert len(hash_password("admin", "admin123")) == 64
    assert hash_password("admin", "admin123") == hash_password("admin", "admin123")


def test_hash_password_sensitif_username():
    """Username berbeda -> hash berbeda."""
    from core.auth import hash_password
    assert hash_password("admin", "pass") != hash_password("other", "pass")


def test_hash_password_lowercase_hex():
    from core.auth import hash_password
    h = hash_password("test", "pass")
    assert h == h.lower()
    assert all(c in "0123456789abcdef" for c in h)


# ── Session lifecycle ────────────────────────────────────────
def test_session_lifecycle():
    from core import auth
    from core.auth import UserSession

    assert auth.get_session() is None
    assert not auth.is_logged_in()

    fake = UserSession(id_user=1, username="u", nama="N", role="admin")
    auth.set_session(fake)
    assert auth.is_logged_in()
    assert auth.get_session() is fake

    auth.clear_session()
    assert auth.get_session() is None
    assert not auth.is_logged_in()


def test_require_session_raises_saat_tidak_login():
    from core import auth
    auth.clear_session()
    with pytest.raises(RuntimeError, match="Belum login"):
        auth.require_session()


def test_require_role_raises_saat_tidak_login():
    from core import auth
    auth.clear_session()
    with pytest.raises(PermissionError, match="belum login"):
        auth.require_role("admin")


def test_require_role_raises_salah_peran():
    from core import auth
    from core.auth import UserSession

    fake = UserSession(id_user=1, username="u", nama="N", role="mahasiswa")
    auth.set_session(fake)
    with pytest.raises(PermissionError, match="peran"):
        auth.require_role("admin")
    auth.clear_session()


def test_require_role_berhasil():
    from core import auth
    from core.auth import UserSession

    fake = UserSession(id_user=1, username="u", nama="N", role="admin")
    auth.set_session(fake)
    result = auth.require_role("admin")
    assert result is fake
    auth.clear_session()


# ── Authenticate ─────────────────────────────────────────────
def test_authenticate_role_tidak_dikenal():
    from core.auth import authenticate
    with pytest.raises(ValueError, match="Peran tidak dikenal"):
        authenticate("u", "p", "superadmin")


def test_authenticate_username_tidak_ditemukan():
    """Tanpa DB: harus return None (tidak raise)."""
    from core.auth import authenticate
    if SKIP_DB:
        pytest.skip(SKIP_REASON)
    result = authenticate("user_tidak_ada_xyz_999", "apa_saja", "admin")
    assert result is None


def test_authenticate_password_salah():
    from core.auth import authenticate
    if SKIP_DB:
        pytest.skip(SKIP_REASON)
    result = authenticate("admin", "password_salah_xxx", "admin")
    assert result is None


@pytest.mark.skipif(SKIP_DB, reason=SKIP_REASON)
def test_authenticate_admin_berhasil():
    from core.auth import authenticate, clear_session
    result = authenticate("admin", "admin123", "admin")
    assert result is not None
    assert result.username == "admin"
    assert result.role == "admin"
    assert result.id_user > 0
    clear_session()


@pytest.mark.skipif(SKIP_DB, reason=SKIP_REASON)
def test_authenticate_mahasiswa_berhasil():
    """Buat data test mahasiswa, autentikasi, bersihkan."""
    import pymysql
    from core.auth import authenticate, hash_password
    from db.connection import execute, get_db, close_db

    nim = f"TEST_{int(time.time())}"
    uname = f"testuser_{int(time.time())}"
    pwd_hash = hash_password(uname, "tes123")

    try:
        execute(
            "INSERT INTO mahasiswa (nim, nama, jenis_kelamin, angkatan, username, password) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (nim, "Test User", "Laki-laki", "2024", uname, pwd_hash),
        )
        result = authenticate(uname, "tes123", "mahasiswa")
        assert result is not None
        assert result.username == uname
        assert result.nim == nim
        assert result.id_mahasiswa is not None
    finally:
        # Bersihkan data test.
        execute("DELETE FROM mahasiswa WHERE username = %s", (uname,))
        close_db()


# ── Maybe rehash ─────────────────────────────────────────────
def test_maybe_rehash_noop():
    from core import auth
    from core.auth import UserSession

    fake = UserSession(id_user=1, username="admin", nama="Admin", role="admin")
    result = auth.maybe_rehash_on_login(fake, "admin", "abc123")
    assert result is False
