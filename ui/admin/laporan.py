"""Laporan: rekap hasil penilaian + export PDF."""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox

import ui.theme as tema
from core import layanan as L
from ui.widgets import HalamanBase, DataTable

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


class LaporanPage(HalamanBase):
    def __init__(self, parent, *, on_pilih, on_logout):
        super().__init__(
            parent, judul="Laporan",
            sub_judul="Rekap hasil penilaian risiko penyebaran hoaks",
            menu=MENU, on_pilih=on_pilih,
            aksi=(("Download PDF", self._export_pdf),),
        )
        self.refresh()

    def refresh(self) -> None:
        try:
            st = L.statistik_dashboard()
            ranking = L.ambil_ranking()
        except Exception as exc:
            self._render_error(str(exc))
            return
        self._render(st, ranking)

    def _render(self, st: dict, ranking: list) -> None:
        k = self.konten
        for c in k.winfo_children():
            c.destroy()

        kartu = tk.Frame(k, bg=tema.CARD,
                         highlightbackground=tema.CARD_BORDER,
                         highlightthickness=1)
        kartu.pack(fill="x", padx=tema.SPACE_XL, pady=tema.SPACE_XL)

        tk.Label(kartu, text="Ringkasan Penilaian", bg=tema.CARD,
                 fg=tema.TEXT,
                 font=tema.FONT_CARD_TITLE).pack(
            anchor="w", padx=tema.SPACE_LG, pady=(tema.SPACE_LG, 0))

        baris_stat = tk.Frame(kartu, bg=tema.CARD)
        baris_stat.pack(fill="x", padx=tema.SPACE_LG, pady=tema.SPACE_BASE)
        info = [
            ("Total Mahasiswa", str(st["total_mahasiswa"]), tema.PRIMARY),
            ("Total Kuesioner", str(st["total_kuesioner"]), tema.INFO),
            ("Hasil Penilaian", str(st["total_penilaian"]), tema.WARNING),
        ]
        for lbl, val, color in info:
            blok = tk.Frame(baris_stat, bg=tema.CARD)
            blok.pack(side="left", padx=(0, tema.SPACE_2XL))
            tk.Label(blok, text=val, bg=tema.CARD, fg=color,
                     font=(tema.FONT_FAMILY, 22, "bold")).pack(anchor="w")
            tk.Label(blok, text=lbl, bg=tema.CARD, fg=tema.TEXT_MUTED,
                     font=tema.FONT_CAPTION).pack(anchor="w")

        baris_dist = tk.Frame(kartu, bg=tema.CARD)
        baris_dist.pack(fill="x", padx=tema.SPACE_LG,
                        pady=(0, tema.SPACE_LG))
        tk.Label(baris_dist, text="Distribusi Kategori:", bg=tema.CARD,
                 fg=tema.TEXT_MUTED,
                 font=tema.FONT_CAPTION).pack(side="left",
                                              padx=(0, tema.SPACE_SM))
        for kat, n in st["distribusi"].items():
            warna = tema.warna_kategori(kat)
            bg = tema.bg_kategori(kat)
            blok = tk.Frame(baris_dist, bg=bg, padx=10, pady=4)
            blok.pack(side="left", padx=(0, tema.SPACE_SM))
            tk.Label(blok, text=f"{n} {kat}", bg=bg, fg=warna,
                     font=tema.FONT_SMALL_BOLD).pack()

        if not ranking:
            tk.Label(k, text="Belum ada data ranking.", bg=tema.BG,
                     fg=tema.TEXT_MUTED,
                     font=tema.FONT_BODY).pack(
                anchor="w", padx=tema.SPACE_XL, pady=tema.SPACE_XL)
            return

        tk.Label(k, text="Ranking Risiko Lengkap", bg=tema.BG,
                 fg=tema.TEXT,
                 font=tema.FONT_CARD_TITLE).pack(
            anchor="w", padx=tema.SPACE_XL,
            pady=(tema.SPACE_BASE, tema.SPACE_SM))

        tabel = DataTable(
            k,
            kolom=[("peringkat", "#"), ("nim", "NIM"), ("nama", "Nama"),
                   ("nilai_risiko", "Nilai Risiko"),
                   ("kategori_risiko", "Kategori")],
            lebar_min=100,
        )
        tabel.pack(fill="both", expand=True,
                   padx=tema.SPACE_XL, pady=(0, tema.SPACE_XL))
        for i, r in enumerate(ranking):
            r["peringkat"] = str(i + 1)
        tabel.isi(ranking)

    def _render_error(self, pesan: str) -> None:
        for c in self.konten.winfo_children():
            c.destroy()
        tk.Label(self.konten, text=f"Gagal memuat laporan:\n{pesan}",
                 bg=tema.BG, fg=tema.DANGER,
                 font=tema.FONT_BODY).pack(
            anchor="w", padx=tema.SPACE_XL, pady=tema.SPACE_2XL)

    def _export_pdf(self) -> None:
        ranking = L.ambil_ranking()
        st = L.statistik_dashboard()
        if not ranking:
            messagebox.showinfo(
                "Tidak ada data", "Proses penilaian dahulu.", parent=self)
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            parent=self,
            title="Simpan Laporan PDF",
        )
        if not path:
            return
        try:
            self._buat_pdf(path, ranking, st)
            messagebox.showinfo("Berhasil", f"Laporan tersimpan di:\n{path}",
                                parent=self)
        except Exception as exc:
            messagebox.showerror("Gagal", f"Gagal membuat PDF:\n{exc}",
                                 parent=self)

    def _buat_pdf(self, path: str, ranking: list, st: dict) -> None:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from reportlab.platypus import (
            SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
        )
        from reportlab.lib.styles import getSampleStyleSheet

        doc = SimpleDocTemplate(path, pagesize=A4,
                                leftMargin=2 * cm, rightMargin=2 * cm,
                                topMargin=2 * cm, bottomMargin=2 * cm)
        styles = getSampleStyleSheet()
        elems = []

        elems.append(Paragraph("Laporan Penilaian Risiko Penyebaran Hoaks",
                               styles["Title"]))
        elems.append(Spacer(1, 0.3 * cm))
        elems.append(Paragraph(
            "Program Studi Ilmu Komputer — Universitas Pattimura",
            styles["Normal"]))
        elems.append(Spacer(1, 0.8 * cm))
        elems.append(Paragraph(
            f"Total mahasiswa: {st['total_mahasiswa']} | "
            f"Kuesioner masuk: {st['total_kuesioner']} | "
            f"Hasil penilaian: {st['total_penilaian']}",
            styles["Normal"]))
        elems.append(Spacer(1, 0.4 * cm))

        data = [["Peringkat", "NIM", "Nama", "Nilai", "Kategori"]]
        for i, r in enumerate(ranking, start=1):
            data.append([
                str(i), r["nim"], r["nama"],
                f"{r['nilai_risiko']:.2f}", r["kategori_risiko"],
            ])

        tbl = Table(data, colWidths=[1.5 * cm, 2.5 * cm, 5 * cm, 2 * cm, 2 * cm])
        style_cmds = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
        ]
        warna_map = {"Rendah": "#dcfce7", "Sedang": "#fef3c7", "Tinggi": "#fee2e2"}
        for i, r in enumerate(ranking, start=1):
            bg = warna_map.get(r["kategori_risiko"], "#ffffff")
            style_cmds.append(("BACKGROUND", (4, i), (4, i), colors.HexColor(bg)))
        tbl.setStyle(TableStyle(style_cmds))
        elems.append(tbl)
        doc.build(elems)
