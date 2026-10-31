"""Fixture bersama: satu App instance untuk seluruh sesi test.

Membuat dan menghancurkan `tk.Tk()` berulang kali tidak stabil di
Windows (Tcl kadang gagal saat inisialisasi ulang), jadi seluruh test
memakai satu `App` yang dibuat sekali di awal sesi. Tiap test me-reset
state login lewat `app.logout()` di awal.
"""

from __future__ import annotations

from tkinter import messagebox

import pytest

import main as m
from core.auth import clear_session


@pytest.fixture(scope="session")
def app():
    """Satu instance `m.App` untuk seluruh sesi test."""
    for n in ("showinfo", "showwarning", "showerror", "askyesno"):
        setattr(messagebox, n, lambda *a, **k: True)
    a = m.App()
    a.withdraw()
    a.update_idletasks()
    yield a
    clear_session()
    a.destroy()
