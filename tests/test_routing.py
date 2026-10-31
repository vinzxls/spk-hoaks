"""Test routing: login -> halaman -> proteksi peran -> logout."""

from __future__ import annotations

import pytest

import ui.admin.dashboard as pg_dash
import ui.mahasiswa.dashboard as pg_mhs
from core.auth import UserSession, clear_session, get_session, set_session
from ui.login import LoginFrame

ADMIN = UserSession(id_user=1, username="admin", nama="Admin", role="admin")
MHS = UserSession(id_user=2, username="mhs1", nama="Mhs Satu",
                  role="mahasiswa", id_mahasiswa=2, nim="001")


@pytest.fixture(autouse=True)
def _reset(app):
    """Setiap test mulai dari state logout yang bersih."""
    clear_session()
    app.logout()
    app.update_idletasks()
    yield
    clear_session()


def _login(a, user):
    set_session(user)
    a._sesudah_login(user)
    a.update_idletasks()


def test_awal_tampil_login(app):
    assert isinstance(app._lapisan.winfo_children()[0], LoginFrame)
    assert app._peran is None
    assert get_session() is None


def test_admin_login_ke_dashboard(app):
    _login(app, ADMIN)
    assert isinstance(app._halaman, pg_dash.DashboardPage)
    assert app._halaman.sidebar._aktif == "dashboard"


@pytest.mark.parametrize("key,expected", [
    ("mahasiswa", "MahasiswaPage"),
    ("kuesioner", "KuesionerPage"),
    ("kriteria", "KriteriaPage"),
    ("hasil", "HasilPage"),
    ("ranking", "RankingPage"),
    ("laporan", "LaporanPage"),
])
def test_admin_bisa_buka_semua_halaman(app, key, expected):
    _login(app, ADMIN)
    app.tampilkan_halaman(key)
    app.update_idletasks()
    assert type(app._halaman).__name__ == expected
    assert app._halaman.sidebar._aktif == key


def test_admin_ditolak_halaman_mahasiswa(app):
    _login(app, ADMIN)
    app._peran = "mahasiswa"
    app.tampilkan_halaman("kuesioner")
    app.update_idletasks()
    assert app._halaman is None
    assert isinstance(app._lapisan.winfo_children()[0], LoginFrame)


def test_mahasiswa_login_ke_dashboard(app):
    _login(app, MHS)
    assert isinstance(app._halaman, pg_mhs.MahasiswaDashboardPage)


def test_mahasiswa_ditolak_halaman_admin(app):
    _login(app, MHS)
    app.tampilkan_halaman("hasil")
    app.update_idletasks()
    assert app._halaman is None or type(app._halaman).__name__ != "HasilPage"


def test_mahasiswa_buka_kuesioner(app):
    _login(app, MHS)
    app.tampilkan_halaman("kuesioner")
    app.update_idletasks()
    assert type(app._halaman).__name__ == "KuesionerPage"


def test_logout_kembali_ke_login(app):
    _login(app, ADMIN)
    app.logout()
    app.update_idletasks()
    assert get_session() is None
    assert app._peran is None
    assert isinstance(app._lapisan.winfo_children()[0], LoginFrame)
