"""Entry point aplikasi: login -> dashboard berdasarkan peran.

Jalankan:  python main.py   (dari folder spk_hoaks)
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox

import config
import ui.theme as tema
from core.auth import (
    clear_session, require_role,
)
from ui.login import LoginFrame

# Halaman admin.
from ui.admin.dashboard import DashboardPage
from ui.admin.mahasiswa import MahasiswaPage
from ui.admin.kuesioner import KuesionerPage as AdminKuesionerPage
from ui.admin.kriteria import KriteriaPage
from ui.admin.hasil import HasilPage
from ui.admin.ranking import RankingPage
from ui.admin.laporan import LaporanPage

# Halaman mahasiswa.
from ui.mahasiswa.dashboard import MahasiswaDashboardPage
from ui.mahasiswa.kuesioner import KuesionerPage as MhsKuesionerPage

KLS_ADMIN = {
    "dashboard": DashboardPage,
    "mahasiswa": MahasiswaPage,
    "kuesioner": AdminKuesionerPage,
    "kriteria": KriteriaPage,
    "hasil": HasilPage,
    "ranking": RankingPage,
    "laporan": LaporanPage,
}

KLS_MHS = {
    "dashboard": MahasiswaDashboardPage,
    "kuesioner": MhsKuesionerPage,
}


class App(tk.Tk):
    """Root aplikasi dengan routing peran."""

    def __init__(self) -> None:
        super().__init__()
        tema.terapkan_tema(self)
        self.title(config.APP_TITLE)
        self.geometry("1280x800")
        self.minsize(1024, 640)

        self._lapisan: tk.Frame | None = None
        self._halaman = None
        self._peran: str | None = None
        self.tampilkan_login()

    def _bersihkan(self) -> None:
        if self._lapisan is not None:
            self._lapisan.destroy()
            self._lapisan = None
        self._halaman = None

    # ── Login ────────────────────────────────────────────────
    def tampilkan_login(self) -> None:
        self._bersihkan()
        self._peran = None
        self._lapisan = tk.Frame(self, bg=tema.BG)
        self._lapisan.pack(fill="both", expand=True)
        LoginFrame(self._lapisan, on_login=self._sesudah_login).pack(
            fill="both", expand=True)

    def _sesudah_login(self, _user) -> None:
        self._peran = _user.role
        self.tampilkan_halaman("dashboard")

    # ── Halaman utama ────────────────────────────────────────
    def tampilkan_halaman(self, kunci: str) -> None:
        if kunci == "logout":
            self.logout()
            return

        if self._peran == "admin":
            try:
                require_role("admin")
            except PermissionError:
                self.tampilkan_login()
                return
            kls = KLS_ADMIN.get(kunci)
            aktif = kunci
        elif self._peran == "mahasiswa":
            try:
                require_role("mahasiswa")
            except PermissionError:
                self.tampilkan_login()
                return
            kls = KLS_MHS.get(kunci)
            aktif = kunci
        else:
            self.tampilkan_login()
            return

        if kls is None:
            messagebox.showwarning("Halaman tidak dikenal",
                                   f"Menu '{kunci}' tidak tersedia untuk peran ini.")
            return

        self._bersihkan()
        self._lapisan = tk.Frame(self, bg=tema.BG)
        self._lapisan.pack(fill="both", expand=True)
        self._halaman = kls(
            self._lapisan,
            on_pilih=self.tampilkan_halaman,
            on_logout=self.logout,
        )
        # Tandai menu aktif di sidebar.
        if hasattr(self._halaman, "sidebar"):
            self._halaman.sidebar.set_aktif(aktif)

    def logout(self) -> None:
        clear_session()
        self.tampilkan_login()


def main() -> None:
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
