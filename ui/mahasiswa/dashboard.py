"""Dashboard mahasiswa: sapaan + tombol mulai kuesioner."""

from __future__ import annotations

import tkinter as tk

import ui.theme as tema
from core import layanan as L
from core.auth import get_session
from ui.widgets import HalamanBase

MENU = (
    ("dashboard", "Dashboard"),
    ("kuesioner", "Kuesioner"),
    ("logout", "Logout"),
)


class MahasiswaDashboardPage(HalamanBase):
    def __init__(self, parent, *, on_pilih, on_logout):
        super().__init__(
            parent, judul="Dashboard", sub_judul="",
            menu=MENU, on_pilih=on_pilih,
        )
        self.refresh()

    def refresh(self) -> None:
        for c in self.konten.winfo_children():
            c.destroy()
        sesi = get_session()
        nama = sesi.nama if sesi else "Mahasiswa"
        nim = sesi.nim if sesi else ""

        tk.Label(self.konten, text=f"Selamat datang, {nama}!",
                 bg=tema.BG, fg=tema.TEXT,
                 font=(tema.FONT_FAMILY, 16, "bold"),
                 anchor="w").pack(fill="x", padx=20, pady=(40, 4))
        tk.Label(self.konten, text=f"NIM: {nim}",
                 bg=tema.BG, fg=tema.TEXT_MUTED,
                 font=(tema.FONT_FAMILY, 11), anchor="w").pack(
            fill="x", padx=20, pady=(0, 20))

        kartu = tk.Frame(self.konten, bg=tema.CARD,
                         highlightbackground=tema.BORDER, highlightthickness=1)
        kartu.pack(fill="x", padx=20, pady=(0, 16))

        sudah = False
        try:
            if sesi:
                sudah = L.sudah_menjawab(int(sesi.id_mahasiswa))
        except Exception:
            pass

        if sudah:
            tk.Label(kartu, text="Kuesioner sudah dikirim",
                     bg=tema.CARD, fg=tema.SUCCESS,
                     font=(tema.FONT_FAMILY, 12, "bold")).pack(
                anchor="w", padx=24, pady=(20, 4))
            tk.Label(kartu,
                     text="Terima kasih telah mengisi kuesioner. "
                          "Jawaban Anda telah disimpan.",
                     bg=tema.CARD, fg=tema.TEXT_MUTED,
                     font=(tema.FONT_FAMILY, 10)).pack(
                anchor="w", padx=24, pady=(0, 20))
        else:
            tk.Label(kartu, text="Silakan isi kuesioner",
                     bg=tema.CARD, fg=tema.TEXT,
                     font=(tema.FONT_FAMILY, 12, "bold")).pack(
                anchor="w", padx=24, pady=(20, 4))
            tk.Label(kartu,
                     text="Kuesioner berisi 30 pertanyaan tentang perilaku "
                          "penyebaran informasi dan pemahaman hoaks.",
                     bg=tema.CARD, fg=tema.TEXT_MUTED,
                     font=(tema.FONT_FAMILY, 10)).pack(
                anchor="w", padx=24, pady=(0, 20))
            tk.Button(
                kartu, text="Mulai Kuesioner", bg=tema.PRIMARY, fg=tema.WHITE,
                font=(tema.FONT_FAMILY, 11, "bold"), relief="flat",
                cursor="hand2", padx=20, pady=10,
                activebackground=tema.PRIMARY_DARK,
                command=lambda: on_pilih("kuesioner"),
            ).pack(anchor="w", padx=24, pady=(0, 20))
