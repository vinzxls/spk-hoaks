"""Ranking risiko: urutan mahasiswa dari nilai tertinggi."""

from __future__ import annotations

import tkinter as tk

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
    ("peringkat", "Peringkat"), ("nim", "NIM"), ("nama", "Nama"),
    ("nilai_risiko", "Nilai Risiko"), ("kategori_risiko", "Kategori"),
)


class RankingPage(HalamanBase):
    def __init__(self, parent, *, on_pilih, on_logout):
        super().__init__(
            parent, judul="Ranking Risiko",
            sub_judul="Urutan mahasiswa berdasarkan nilai risiko",
            menu=MENU, on_pilih=on_pilih,
            aksi=(("Perbarui", self.refresh),),
        )
        top = tk.Frame(self.konten, bg=tema.BG)
        top.pack(fill="x", padx=20, pady=(20, 8))
        self._cari = SearchBox(top, placeholder="Cari nama atau NIM...",
                               on_cari=lambda _q: self._muat())
        self._cari.pack(side="left")
        self._tabel = DataTable(self.konten, kolom=KOLOM)
        self._tabel.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.refresh()

    def refresh(self) -> None:
        self._muat()

    def _muat(self) -> None:
        try:
            data = L.ambil_ranking()
        except Exception as exc:
            self._tabel.set_kosong(f"Gagal memuat: {exc}")
            return
        cari = self._cari.get().lower()
        if cari:
            data = [d for d in data
                    if cari in d["nama"].lower() or cari in d["nim"].lower()]
        if not data:
            self._tabel.set_kosong("Belum ada ranking. Proses penilaian dahulu.")
            return
        self._tabel.isi([
            {"peringkat": d["peringkat"], "nim": d["nim"], "nama": d["nama"],
             "nilai_risiko": f"{d['nilai_risiko']:.2f}",
             "kategori_risiko": d["kategori_risiko"]}
            for d in data
        ])
        for item, d in zip(self._tabel.tree.get_children(), data):
            kat = d["kategori_risiko"]
            tag = f"r_{kat}"
            self._tabel.tree.tag_configure(
                tag, background=tema.bg_kategori(kat),
                foreground=tema.warna_kategori(kat))
            self._tabel.tree.item(item, tags=(tag,))
