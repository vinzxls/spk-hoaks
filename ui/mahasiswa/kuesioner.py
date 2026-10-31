"""Halaman kuesioner mahasiswa: pertanyaan Likert 1-5 + konfirmasi."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox

import ui.theme as tema
from core import layanan as L
from core.auth import get_session
from ui.widgets import HalamanBase

MENU = (
    ("dashboard", "Dashboard"),
    ("kuesioner", "Kuesioner"),
    ("logout", "Logout"),
)

LIKERT_LABELS = {
    1: "Sangat tidak setuju",
    2: "Tidak setuju",
    3: "Netral",
    4: "Setuju",
    5: "Sangat setuju",
}


class KuesionerPage(HalamanBase):
    def __init__(self, parent, *, on_pilih, on_logout):
        super().__init__(
            parent, judul="Kuesioner", sub_judul="",
            menu=MENU, on_pilih=on_pilih,
        )
        self._on_pilih = on_pilih
        self._vars: dict[str, tk.IntVar] = {}
        self.refresh()

    def refresh(self) -> None:
        for c in self.konten.winfo_children():
            c.destroy()
        self._vars.clear()

        sesi = get_session()
        if sesi is None:
            return

        if L.sudah_menjawab(int(sesi.id_mahasiswa)):
            self._selesai()
            return

        try:
            subs = L.ambil_semua_subkriteria()
        except Exception as exc:
            tk.Label(self.konten, text=f"Gagal memuat kuesioner:\n{exc}",
                     bg=tema.BG, fg=tema.DANGER,
                     font=(tema.FONT_FAMILY, 11)).pack(anchor="w", padx=20, pady=40)
            return

        # Header.
        tk.Label(self.konten,
                 text="Jawab pertanyaan berikut sesuai kondisi Anda saat ini.",
                 bg=tema.BG, fg=tema.TEXT_MUTED,
                 font=(tema.FONT_FAMILY, 10), anchor="w",
                 wraplength=560).pack(fill="x", padx=20, pady=(24, 8))

        # Pertanyaan.
        for sub in subs:
            kode = sub["kode_sub"]
            self._vars[kode] = tk.IntVar(value=0)

            kartu = tk.Frame(self.konten, bg=tema.CARD,
                             highlightbackground=tema.BORDER,
                             highlightthickness=1)
            kartu.pack(fill="x", padx=20, pady=(0, 6))

            tk.Label(
                kartu, text=f"{sub['kode_sub']}  {sub['nama_subkriteria']}",
                bg=tema.CARD, fg=tema.TEXT,
                font=(tema.FONT_FAMILY, 10, "bold"), anchor="w",
                wraplength=540, justify="left",
            ).pack(anchor="w", padx=20, pady=(14, 6))

            radio_frame = tk.Frame(kartu, bg=tema.CARD)
            radio_frame.pack(anchor="w", padx=20, pady=(0, 14))
            for val, lbl in LIKERT_LABELS.items():
                rb = tk.Radiobutton(
                    radio_frame, text=lbl, variable=self._vars[kode],
                    value=val, bg=tema.CARD, fg=tema.TEXT_MUTED,
                    activebackground=tema.CARD, font=(tema.FONT_FAMILY, 9),
                    selectcolor=tema.WHITE,
                )
                rb.pack(side="left", padx=(0, 8))

        # Tombol kirim.
        footer = tk.Frame(self.konten, bg=tema.BG)
        footer.pack(fill="x", padx=20, pady=(16, 20))
        tk.Button(
            footer, text="Kirim Jawaban", bg=tema.PRIMARY, fg=tema.WHITE,
            font=(tema.FONT_FAMILY, 11, "bold"), relief="flat",
            padx=24, pady=10, cursor="hand2",
            activebackground=tema.PRIMARY_DARK,
            command=self._kirim,
        ).pack(side="right")
        tk.Button(
            footer, text="Bersihkan", bg=tema.WHITE, fg=tema.TEXT,
            font=(tema.FONT_FAMILY, 10), relief="solid", bd=1,
            padx=16, pady=10, cursor="hand2",
            command=self.refresh,
        ).pack(side="right", padx=(0, 10))

    def _kirim(self) -> None:
        sesi = get_session()
        if sesi is None:
            return
        belum = [k for k, v in self._vars.items() if v.get() == 0]
        if belum:
            messagebox.showwarning(
                "Belum lengkap",
                f"Masih ada {len(belum)} pertanyaan yang belum dijawab.",
                parent=self)
            return
        jawaban = {k: v.get() for k, v in self._vars.items()}
        try:
            L.simpan_jawaban(int(sesi.id_mahasiswa), jawaban)
        except Exception as exc:
            messagebox.showerror("Gagal", str(exc), parent=self)
            return
        self._selesai()

    def _selesai(self) -> None:
        for c in self.konten.winfo_children():
            c.destroy()

        tk.Frame(self.konten, bg=tema.SUCCESS, width=100, height=100).pack(
            pady=(80, 20))
        tk.Label(self.konten, text="Kuesioner Berhasil Dikirim",
                 bg=tema.BG, fg=tema.SUCCESS,
                 font=(tema.FONT_FAMILY, 18, "bold")).pack(pady=(0, 8))
        tk.Label(self.konten,
                 text="Terima kasih! Jawaban Anda telah disimpan.",
                 bg=tema.BG, fg=tema.TEXT_MUTED,
                 font=(tema.FONT_FAMILY, 11)).pack(pady=(0, 30))
        tk.Button(
            self.konten, text="Kembali ke Dashboard", bg=tema.PRIMARY,
            fg=tema.WHITE, font=(tema.FONT_FAMILY, 11, "bold"),
            relief="flat", padx=24, pady=10, cursor="hand2",
            activebackground=tema.PRIMARY_DARK,
            command=lambda: self._on_pilih("dashboard"),
        ).pack()
