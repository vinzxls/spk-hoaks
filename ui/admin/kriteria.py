"""Kelola kriteria & subkriteria (master-detail, sesuai mockup klien)."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

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

KOLOM_KRITERIA = (
    ("no", "No"),
    ("kode_kriteria", "Kode"),
    ("nama_kriteria", "Nama Kriteria"),
    ("jumlah", "Jumlah Subkriteria"),
)

KOLOM_SUB = (
    ("kode_sub", "Kode"),
    ("nama_subkriteria", "Nama Subkriteria"),
)


class KriteriaPage(HalamanBase):
    def __init__(self, parent, *, on_pilih, on_logout):
        super().__init__(
            parent,
            judul="Kriteria & Subkriteria",
            sub_judul="Kelola kriteria dan subkriteria penelitian",
            menu=MENU,
            on_pilih=on_pilih,
        )
        self._kriteria_terpilih: dict | None = None
        self._bangun()
        self.refresh()

    # ── Layout ──────────────────────────────────────────────
    def _bangun(self) -> None:
        atas = tk.Frame(self.konten, bg=tema.BG)
        atas.pack(fill="x", padx=20, pady=(20, 10))
        self._cari = SearchBox(
            atas, placeholder="Cari nama kriteria...",
            on_cari=lambda _q: self._muat_kriteria(),
        )
        self._cari.pack(side="left")
        ttk.Button(
            atas, text="Tambah Kriteria", style="Primary.TButton",
            command=self._tambah_kriteria,
        ).pack(side="right")

        badan = tk.Frame(self.konten, bg=tema.BG)
        badan.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Panel kiri: daftar kriteria.
        kiri = tk.Frame(badan, bg=tema.CARD, highlightbackground=tema.BORDER,
                        highlightthickness=1)
        kiri.pack(side="left", fill="both", expand=True)
        tk.Label(kiri, text="Kriteria", bg=tema.CARD, fg=tema.TEXT,
                 font=(tema.FONT_FAMILY, 12, "bold"),
                 anchor="w").pack(fill="x", padx=16, pady=(14, 8))
        self._tabel_kriteria = DataTable(
            kiri, kolom=KOLOM_KRITERIA, on_klik=self._pilih_kriteria)
        self._tabel_kriteria.pack(fill="both", expand=True,
                                  padx=16, pady=(0, 8))
        self._tabel_kriteria.tree.bind("<Double-1>", lambda _e: self._edit_kriteria())
        baris_kiri = tk.Frame(kiri, bg=tema.CARD)
        baris_kiri.pack(fill="x", padx=16, pady=(0, 14))
        ttk.Button(baris_kiri, text="Edit", style="Secondary.TButton",
                   command=self._edit_kriteria).pack(side="left", padx=(0, 6))
        ttk.Button(baris_kiri, text="Hapus", style="Danger.TButton",
                   command=self._hapus_kriteria).pack(side="left")

        # Panel kanan: subkriteria dari kriteria terpilih.
        kanan = tk.Frame(badan, bg=tema.CARD, highlightbackground=tema.BORDER,
                         highlightthickness=1)
        kanan.pack(side="left", fill="both", expand=True, padx=(12, 0))
        self._judul_sub = tk.Label(
            kanan, text="Subkriteria", bg=tema.CARD, fg=tema.TEXT,
            font=(tema.FONT_FAMILY, 12, "bold"), anchor="w")
        self._judul_sub.pack(fill="x", padx=16, pady=(14, 8))
        self._tabel_sub = DataTable(
            kanan, kolom=KOLOM_SUB, on_klik=self._pilih_sub)
        self._tabel_sub.pack(fill="both", expand=True, padx=16, pady=(0, 8))
        self._tabel_sub.tree.bind("<Double-1>", lambda _e: self._edit_sub())
        baris_kanan = tk.Frame(kanan, bg=tema.CARD)
        baris_kanan.pack(fill="x", padx=16, pady=(0, 14))
        ttk.Button(baris_kanan, text="Tambah Subkriteria",
                   style="Primary.TButton",
                   command=self._tambah_sub).pack(side="left", padx=(0, 6))
        ttk.Button(baris_kanan, text="Edit", style="Secondary.TButton",
                   command=self._edit_sub).pack(side="left", padx=(0, 6))
        ttk.Button(baris_kanan, text="Hapus", style="Danger.TButton",
                   command=self._hapus_sub).pack(side="left")

    # ── Data ────────────────────────────────────────────────
    def refresh(self) -> None:
        self._muat_kriteria()

    def _muat_kriteria(self) -> None:
        try:
            data = L.ambil_kriteria_dengan_sub()
        except Exception as exc:
            self._tabel_kriteria.set_kosong(f"Gagal memuat: {exc}")
            return
        cari = self._cari.get().lower()
        if cari:
            data = [k for k in data
                    if cari in k["nama_kriteria"].lower()
                    or cari in k["kode_kriteria"].lower()]
        if not data:
            self._tabel_kriteria.set_kosong("Belum ada kriteria.")
            self._kriteria_terpilih = None
            self._muat_sub()
            return
        self._tabel_kriteria.isi([
            {"no": i, "kode_kriteria": k["kode_kriteria"],
             "nama_kriteria": k["nama_kriteria"],
             "jumlah": len(k["subkriteria"])}
            for i, k in enumerate(data, start=1)
        ])
        if not self._kriteria_terpilih:
            first = data[0]
            self._kriteria_terpilih = {
                "id_kriteria": first["id_kriteria"],
                "kode_kriteria": first["kode_kriteria"],
                "nama_kriteria": first["nama_kriteria"],
            }
            self._muat_sub()
            return
        self._muat_sub()

    def _muat_sub(self) -> None:
        if not self._kriteria_terpilih:
            self._judul_sub.config(text="Subkriteria")
            self._tabel_sub.set_kosong("Pilih kriteria di panel kiri.")
            return
        k = self._kriteria_terpilih
        self._judul_sub.config(
            text=f"Subkriteria — {k['kode_kriteria']} {k['nama_kriteria']}")
        try:
            semua = L.ambil_kriteria_dengan_sub()
        except Exception as exc:
            self._tabel_sub.set_kosong(f"Gagal memuat: {exc}")
            return
        saat_ini = next(
            (x for x in semua if x["id_kriteria"] == k["id_kriteria"]), None)
        subs = saat_ini["subkriteria"] if saat_ini else []
        if not subs:
            self._tabel_sub.set_kosong("Belum ada subkriteria.")
            return
        self._tabel_sub.isi([
            {"kode_sub": s["kode_sub"], "nama_subkriteria": s["nama_subkriteria"]}
            for s in subs
        ])

    # ── Dialog input ────────────────────────────────────────
    def _dialog_nama(self, judul: str, awal: str) -> str | None:
        dlg = tk.Toplevel(self)
        dlg.title(judul)
        dlg.configure(bg=tema.BG)
        dlg.transient(self)
        dlg.grab_set()
        f = tk.Frame(dlg, bg=tema.CARD, padx=24, pady=20)
        f.pack(fill="both", expand=True)
        tk.Label(f, text=judul, bg=tema.CARD, fg=tema.TEXT,
                 font=(tema.FONT_FAMILY, 13, "bold")).pack(anchor="w",
                                                            pady=(0, 12))
        e = tk.Entry(f, font=(tema.FONT_FAMILY, 11), width=44, relief="solid",
                     bd=1, highlightthickness=0,
                     highlightbackground=tema.BORDER)
        e.pack(fill="x", ipady=6)
        e.insert(0, awal)
        e.select_range(0, "end")
        e.focus_set()
        out: dict[str, str] = {}

        def ok() -> None:
            v = e.get().strip()
            if v:
                out["nilai"] = v
            dlg.destroy()

        baris = tk.Frame(f, bg=tema.CARD)
        baris.pack(fill="x", pady=(16, 0))
        ttk.Button(baris, text="Simpan", style="Primary.TButton",
                   command=ok).pack(side="right", padx=(0, 8))
        ttk.Button(baris, text="Batal", style="Secondary.TButton",
                   command=dlg.destroy).pack(side="right")
        e.bind("<Return>", lambda _ev: ok())
        self.wait_window(dlg)
        return out.get("nilai")

    # ── Kriteria: tambah / edit / hapus ─────────────────────
    def _tambah_kriteria(self) -> None:
        v = self._dialog_nama("Nama Kriteria", "")
        if not v:
            return
        try:
            L.simpan_kriteria(v)
            self._kriteria_terpilih = None
            self._cari.clear()
            self._muat_kriteria()
        except Exception as exc:
            messagebox.showerror("Gagal", str(exc), parent=self)

    def _pilih_kriteria(self, _baris: dict) -> None:
        kode = _baris.get("kode_kriteria")
        if not kode:
            return
        try:
            semua = L.ambil_kriteria_dengan_sub()
        except Exception:
            return
        k = next((x for x in semua if x["kode_kriteria"] == kode), None)
        if k:
            self._kriteria_terpilih = {
                "id_kriteria": k["id_kriteria"],
                "kode_kriteria": k["kode_kriteria"],
                "nama_kriteria": k["nama_kriteria"],
            }
            self._muat_sub()

    def _edit_kriteria(self) -> None:
        baris = self._tabel_kriteria.baris_terpilih()
        if not baris:
            messagebox.showinfo(
                "Pilih kriteria", "Pilih kriteria yang akan diedit.", parent=self)
            return
        self._pilih_kriteria(baris)
        k = self._kriteria_terpilih
        if not k:
            return
        v = self._dialog_nama("Edit Kriteria", k["nama_kriteria"])
        if not v or v == k["nama_kriteria"]:
            return
        try:
            L.simpan_kriteria(v, int(k["id_kriteria"]))
            self._kriteria_terpilih = {**k, "nama_kriteria": v}
            self._muat_kriteria()
        except Exception as exc:
            messagebox.showerror("Gagal", str(exc), parent=self)

    def _hapus_kriteria(self) -> None:
        baris = self._tabel_kriteria.baris_terpilih()
        if not baris:
            messagebox.showinfo(
                "Pilih kriteria", "Pilih kriteria yang akan dihapus.", parent=self)
            return
        self._pilih_kriteria(baris)
        k = self._kriteria_terpilih
        if not k:
            return
        n_sub = self._tabel_sub.tree.get_children()
        n_sub = len(n_sub)
        peringatan = (f"Kriteria '{k['kode_kriteria']} {k['nama_kriteria']}' "
                      f"dan {n_sub} subkriteria di bawahnya akan dihapus.")
        if n_sub:
            peringatan += ("\n\nJawaban mahasiswa pada subkriteria tersebut juga "
                           "akan terhapus dan penilaian dihitung ulang.")
        if not messagebox.askyesno("Konfirmasi Hapus", peringatan, parent=self):
            return
        try:
            L.hapus_kriteria(int(k["id_kriteria"]))
            self._kriteria_terpilih = None
            self._muat_kriteria()
        except Exception as exc:
            messagebox.showerror("Gagal", str(exc), parent=self)

    # ── Subkriteria: tambah / edit / hapus ──────────────────
    def _tambah_sub(self) -> None:
        if not self._kriteria_terpilih:
            messagebox.showinfo(
                "Pilih kriteria", "Pilih kriteria terlebih dahulu.", parent=self)
            return
        v = self._dialog_nama(
            f"Nama Subkriteria ({self._kriteria_terpilih['kode_kriteria']})", "")
        if not v:
            return
        try:
            L.simpan_subkriteria(int(self._kriteria_terpilih["id_kriteria"]), v)
            self._muat_kriteria()
        except Exception as exc:
            messagebox.showerror("Gagal", str(exc), parent=self)

    def _sub_terpilih(self) -> dict | None:
        baris = self._tabel_sub.baris_terpilih()
        if not baris or not self._kriteria_terpilih:
            return None
        kode = baris.get("kode_sub")
        if not kode:
            return None
        semua = L.ambil_semua_subkriteria()
        return next((s for s in semua if s["kode_sub"] == kode), None)

    def _pilih_sub(self, _baris: dict) -> None:
        pass

    def _edit_sub(self) -> None:
        s = self._sub_terpilih()
        if s is None:
            messagebox.showinfo(
                "Pilih subkriteria",
                "Pilih subkriteria yang akan diedit.", parent=self)
            return
        v = self._dialog_nama("Edit Subkriteria", s["nama_subkriteria"])
        if not v or v == s["nama_subkriteria"]:
            return
        try:
            L.simpan_subkriteria(int(s["id_kriteria"]), v,
                                 int(s["id_subkriteria"]))
            self._muat_kriteria()
        except Exception as exc:
            messagebox.showerror("Gagal", str(exc), parent=self)

    def _hapus_sub(self) -> None:
        s = self._sub_terpilih()
        if s is None:
            messagebox.showinfo(
                "Pilih subkriteria",
                "Pilih subkriteria yang akan dihapus.", parent=self)
            return
        if not messagebox.askyesno(
            "Konfirmasi Hapus",
            f"Hapus subkriteria '{s['kode_sub']} {s['nama_subkriteria']}'?\n"
            "Jawaban mahasiswa pada subkriteria ini juga terhapus.",
            parent=self,
        ):
            return
        try:
            L.hapus_subkriteria(int(s["id_subkriteria"]))
            self._muat_kriteria()
        except Exception as exc:
            messagebox.showerror("Gagal", str(exc), parent=self)
