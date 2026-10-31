"""Dashboard admin: kartu statistik, donat distribusi, top 5 ranking."""

from __future__ import annotations

import tkinter as tk
from typing import Callable

import ui.theme as tema
from core import layanan as L
from ui.widgets import DataTable, DonutChart, HalamanBase, Legend, StatCard

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


class DashboardPage(HalamanBase):
    def __init__(self, parent, *, on_pilih, on_logout):
        super().__init__(
            parent, judul="Dashboard", sub_judul="Ringkasan penilaian risiko",
            menu=MENU, on_pilih=on_pilih,
            aksi=(("Perbarui", self.refresh),),
        )
        self._bangun()
        self.refresh()

    def _bangun(self) -> None:
        k = self.konten
        # Baris kartu statistik.
        self._kartu = tk.Frame(k, bg=tema.BG)
        self._kartu.pack(fill="x", padx=20, pady=(20, 8))
        self._stat: dict[str, StatCard] = {}
        for key, label, accent in (
            ("total_mahasiswa", "Total Mahasiswa", tema.PRIMARY),
            ("total_kuesioner", "Kuesioner Masuk", tema.INFO),
            ("total_penilaian", "Hasil Penilaian", tema.WARNING),
            ("total_ranking", "Ranking Risiko", tema.DANGER),
        ):
            c = StatCard(self._kartu, label=label, value="-", accent=accent)
            c.pack(side="left", fill="both", expand=True, padx=(0, 12))
            self._stat[key] = c

        # Baris bawah: donat + top 5.
        bawah = tk.Frame(k, bg=tema.BG)
        bawah.pack(fill="both", expand=True, padx=20, pady=(8, 20))

        kiri = tk.Frame(bawah, bg=tema.CARD, highlightbackground=tema.BORDER,
                        highlightthickness=1)
        kiri.pack(side="left", fill="both", expand=True)
        tk.Label(kiri, text="Distribusi Tingkat Risiko", bg=tema.CARD,
                 fg=tema.TEXT, font=(tema.FONT_FAMILY, 12, "bold"),
                 anchor="w").pack(fill="x", padx=20, pady=(18, 4))
        self._donut = DonutChart(kiri, ukuran=200, tebal=40)
        self._donat_wrap = tk.Frame(kiri, bg=tema.CARD)
        self._donat_wrap.pack(pady=(0, 18))
        self._donut.pack(in_=self._donat_wrap, side="left", padx=(20, 8))
        self._legend = Legend(self._donat_wrap)
        self._legend.pack(side="left", padx=(0, 20), anchor="center")

        kanan = tk.Frame(bawah, bg=tema.CARD, highlightbackground=tema.BORDER,
                         highlightthickness=1)
        kanan.pack(side="left", fill="both", expand=True, padx=(12, 0))
        tk.Label(kanan, text="Ranking Risiko (Top 5)", bg=tema.CARD,
                 fg=tema.TEXT, font=(tema.FONT_FAMILY, 12, "bold"),
                 anchor="w").pack(fill="x", padx=20, pady=(18, 8))
        self._tabel = DataTable(kanan, kolom=(
            ("peringkat", "#"), ("nama", "Nama"), ("nilai_risiko", "Nilai"),
        ))
        self._tabel.pack(fill="both", expand=True, padx=20, pady=(0, 20))

    def refresh(self) -> None:
        """Muat ulang semua angka. Pipeline FAHP berjalan otomatis di sini."""
        try:
            L.hitung_semua_penilaian()
            st = L.statistik_dashboard()
        except Exception as exc:  # DB mungkin mati
            self._tampilkan_gagal(str(exc))
            return
        self._kartu_stat(st)
        self._kartu_donat(st["distribusi"])
        self._kartu_top5()

    def _tampilkan_gagal(self, pesan: str) -> None:
        for c in self._stat.values():
            c.set_value("-")
        self._donut.gambar({}, tema.KATEGORI_WARNA)
        self._legend.isi({}, {})
        self._tabel.set_kosong(f"Gagal memuat data: {pesan[:80]}")

    def _kartu_stat(self, st: dict) -> None:
        self._stat["total_mahasiswa"].set_value(str(st["total_mahasiswa"]))
        self._stat["total_kuesioner"].set_value(str(st["total_kuesioner"]))
        self._stat["total_penilaian"].set_value(str(st["total_penilaian"]))
        self._stat["total_ranking"].set_value(str(st["total_ranking"]))

    def _kartu_donat(self, distribusi: dict) -> None:
        self._donut.gambar(distribusi, tema.KATEGORI_WARNA, judul="Mahasiswa")
        self._legend.isi(distribusi, tema.KATEGORI_WARNA)

    def _kartu_top5(self) -> None:
        try:
            data = L.ambil_ranking()[:5]
        except Exception:
            data = []
        if not data:
            self._tabel.set_kosong("Belum ada hasil penilaian.")
            return
        self._tabel.isi([
            {"peringkat": r["peringkat"], "nama": r["nama"],
             "nilai_risiko": f"{r['nilai_risiko']:.2f}"}
            for r in data
        ])
