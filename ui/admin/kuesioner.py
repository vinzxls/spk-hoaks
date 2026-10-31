"""Viewer data kuesioner yang masuk."""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

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
    ("nim", "NIM"), ("nama", "Nama"),
    ("jumlah", "Jawaban"), ("terakhir", "Waktu Pengisian"),
)


class KuesionerPage(HalamanBase):
    def __init__(self, parent, *, on_pilih, on_logout):
        super().__init__(
            parent, judul="Data Kuesioner",
            sub_judul="Jawaban mahasiswa yang telah dikirim",
            menu=MENU, on_pilih=on_pilih,
            aksi=(("Lihat Detail", self._detail),
                  ("Export Excel", self._export_excel)),
        )
        top = tk.Frame(self.konten, bg=tema.BG)
        top.pack(fill="x", padx=20, pady=(20, 8))
        self._cari = SearchBox(top, placeholder="Cari nama atau NIM...",
                               on_cari=lambda _q: self._muat())
        self._cari.pack(side="left")
        self._tabel = DataTable(self.konten, kolom=KOLOM, on_klik=self._detail)
        self._tabel.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self._muat()

    def refresh(self) -> None:
        self._muat()

    def _muat(self) -> None:
        try:
            data = L.ambil_daftar_pengisi()
        except Exception as exc:
            self._tabel.set_kosong(f"Gagal memuat: {exc}")
            return
        cari = self._cari.get().lower()
        if cari:
            data = [d for d in data
                    if cari in d["nama"].lower() or cari in d["nim"].lower()]
        if not data:
            self._tabel.set_kosong("Belum ada kuesioner yang masuk.")
            return
        self._tabel.isi([
            {"nim": d["nim"], "nama": d["nama"], "jumlah": d["jumlah"],
             "terakhir": str(d["terakhir"])}
            for d in data
        ])

    def _export_excel(self) -> None:
        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")],
            parent=self,
            title="Export Jawaban untuk SPSS",
            initialfile="kuesioner_spss.xlsx",
        )
        if not path:
            return
        try:
            n = L.export_ke_excel(path)
        except ValueError as exc:
            messagebox.showinfo("Tidak ada data", str(exc), parent=self)
            return
        except Exception as exc:
            messagebox.showerror("Gagal", f"Gagal export Excel:\n{exc}",
                                 parent=self)
            return
        messagebox.showinfo(
            "Berhasil",
            f"{n} mahasiswa di-export ke:\n{path}\n\n"
            "Format: NIM | Nama | Butir 1-30 (skor Likert 1-5)\n"
            "Siap diimpor ke SPSS untuk uji reliabilitas & validitas.",
            parent=self,
        )

    def _detail(self, _baris: dict | None = None) -> None:
        baris = _baris or self._tabel.baris_terpilih()
        if not baris:
            messagebox.showinfo("Pilih data", "Pilih mahasiswa terlebih dahulu.",
                                parent=self)
            return
        semua = L.ambil_daftar_pengisi()
        target = next((d for d in semua if d["nim"] == baris["nim"]), None)
        if target is None:
            return
        jawaban = L.ambil_jawaban_mahasiswa(int(target["id_mahasiswa"]))
        sub = {r["kode_sub"]: r["nama_subkriteria"]
               for r in L.ambil_semua_subkriteria()}

        dlg = tk.Toplevel(self)
        dlg.title(f"Jawaban {target['nama']}")
        dlg.configure(bg=tema.BG)
        dlg.geometry("620x560")
        dlg.transient(self)
        tk.Label(
            dlg, text=f"Jawaban Kuesioner — {target['nama']} ({target['nim']})",
            bg=tema.BG, fg=tema.TEXT,
            font=(tema.FONT_FAMILY, 13, "bold"),
        ).pack(anchor="w", padx=20, pady=(18, 12))

        frame = tk.Frame(dlg, bg=tema.CARD, highlightbackground=tema.BORDER,
                         highlightthickness=1)
        frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        canvas = tk.Canvas(frame, bg=tema.CARD, highlightthickness=0)
        sb = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        inner = tk.Frame(canvas, bg=tema.CARD)
        win = canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>",
                   lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfigure(win, width=e.width))

        for kode, nama in sorted(sub.items()):
            row = tk.Frame(inner, bg=tema.CARD)
            row.pack(fill="x", padx=16, pady=5)
            tk.Label(row, text=f"{kode}  {nama}", bg=tema.CARD, fg=tema.TEXT,
                     font=(tema.FONT_FAMILY, 10), anchor="w",
                     wraplength=400, justify="left").pack(side="left",
                                                          fill="x", expand=True)
            skor = jawaban.get(kode)
            tk.Label(row, text=str(skor) if skor is not None else "-",
                     bg=tema.PRIMARY_LIGHT, fg=tema.PRIMARY_DARK,
                     font=(tema.FONT_FAMILY, 11, "bold"),
                     padx=12, pady=2).pack(side="right")
