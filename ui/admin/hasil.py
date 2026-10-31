"""Hasil penilaian: nilai risiko + kategori per mahasiswa."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox

import ui.theme as tema
from core import layanan as L
from ui.widgets import DataTable, HalamanBase, SearchBox

MENU = (
    ("dashboard", "Dashboard"),
    ("mahasiswa", "Data Mahasiswa"),
    ("kuesioner", "Data Kuesioner"),
    ("kriteria", "Kriteria & Subkriteria"),
    ("hasil", "Hasil Penilaian"),
    ("ranking", "Ranking Risiko"),
    ("laporan", "Laporan"),
    ("logout", "Logout"),
)

KOLOM = (
    ("peringkat", "#"), ("nim", "NIM"), ("nama", "Nama"),
    ("nilai_risiko", "Nilai Risiko"), ("kategori_risiko", "Kategori"),
)


class HasilPage(HalamanBase):
    def __init__(self, parent, *, on_pilih, on_logout):
        super().__init__(
            parent, judul="Hasil Penilaian",
            sub_judul="Nilai dan kategori risiko setiap mahasiswa",
            menu=MENU, on_pilih=on_pilih,
            aksi=(
                ("Proses Penilaian", self.proses),
                ("Perbarui", self.refresh),
            ),
        )
        top = tk.Frame(self.konten, bg=tema.BG)
        top.pack(fill="x", padx=20, pady=(20, 8))
        self._cari = SearchBox(top, placeholder="Cari nama atau NIM...",
                               on_cari=lambda _q: self._muat())
        self._cari.pack(side="left")
        self._tabel = DataTable(self.konten, kolom=KOLOM)
        self._tabel.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.refresh()

    def proses(self) -> None:
        """Jalankan Fuzzy AHP + penilaian otomatis (tidak ada menu hitung manual)."""
        try:
            n = L.hitung_semua_penilaian()
        except Exception as exc:
            messagebox.showerror("Gagal", str(exc), parent=self)
            return
        messagebox.showinfo(
            "Penilaian Selesai",
            f"{n} mahasiswa telah dinilai.\nBobot Fuzzy AHP dihitung otomatis.",
            parent=self)
        self.refresh()

    def refresh(self) -> None:
        self._muat()

    def _muat(self) -> None:
        try:
            data = L.ambil_hasil_penilaian()
        except Exception as exc:
            self._tabel.set_kosong(f"Gagal memuat: {exc}")
            return
        cari = self._cari.get().lower()
        if cari:
            data = [d for d in data
                    if cari in d["nama"].lower() or cari in d["nim"].lower()]
        if not data:
            self._tabel.set_kosong("Belum ada hasil penilaian.")
            return
        self._tabel.isi([
            {"peringkat": d["peringkat"], "nim": d["nim"], "nama": d["nama"],
             "nilai_risiko": f"{d['nilai_risiko']:.2f}",
             "kategori_risiko": d["kategori_risiko"]}
            for d in data
        ])
        self._warnai_kategori(data)

    def _warnai_kategori(self, data: list) -> None:
        """Warnai kolom kategori dengan badge berwarna di baris tabel."""
        if not hasattr(self._tabel, "tree"):
            return
        items = self._tabel.tree.get_children()
        for item, d in zip(items, data):
            warna = tema.warna_kategori(d["kategori_risiko"])
            bg = tema.bg_kategori(d["kategori_risiko"])
            self._tabel.tree.tag_configure(
                f"k_{d['kategori_risiko']}", background=bg, foreground=warna)
            self._tabel.tree.item(item, tags=(f"k_{d['kategori_risiko']}",))
