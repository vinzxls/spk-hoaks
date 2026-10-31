"""CRUD data mahasiswa."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

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
    ("jenis_kelamin", "Jenis Kelamin"), ("angkatan", "Angkatan"),
)


class MahasiswaPage(HalamanBase):
    def __init__(self, parent, *, on_pilih, on_logout):
        super().__init__(
            parent, judul="Data Mahasiswa",
            sub_judul="Kelola data mahasiswa",
            menu=MENU, on_pilih=on_pilih,
            aksi=(
                ("Tambah", self._tambah),
                ("Edit", self._edit),
                ("Hapus", self._hapus),
            ),
        )
        top = tk.Frame(self.konten, bg=tema.BG)
        top.pack(fill="x", padx=20, pady=(20, 8))
        self._cari = SearchBox(top, placeholder="Cari nama atau NIM...",
                               on_cari=lambda _q: self._muat())
        self._cari.pack(side="left")

        self._tabel = DataTable(self.konten, kolom=KOLOM, on_klik=self._pilih)
        self._tabel.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self._muat()

    def refresh(self) -> None:
        self._muat()

    def _muat(self) -> None:
        try:
            data = L.ambil_semua_mahasiswa(self._cari.get())
        except Exception as exc:
            self._tabel.set_kosong(f"Gagal memuat: {exc}")
            return
        if not data:
            self._tabel.set_kosong("Belum ada data mahasiswa.")
            return
        self._tabel.isi(data)

    def _pilih(self, _baris: dict) -> None:
        pass

    def _form_dialog(self, judul: str, awal: dict) -> dict | None:
        dlg = tk.Toplevel(self)
        dlg.title(judul)
        dlg.configure(bg=tema.BG)
        dlg.transient(self)
        dlg.grab_set()
        dlg.resizable(False, False)

        hasil: dict = {}
        f = tk.Frame(dlg, bg=tema.CARD, padx=24, pady=20)
        f.pack(fill="both", expand=True)
        tk.Label(f, text=judul, bg=tema.CARD, fg=tema.TEXT,
                 font=(tema.FONT_FAMILY, 13, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 16))

        fields = [
            ("nim", "NIM"), ("nama", "Nama Lengkap"),
            ("jenis_kelamin", "Jenis Kelamin"), ("angkatan", "Angkatan"),
            ("username", "Username"),
        ]
        entries: dict[str, tk.Entry] = {}
        for i, (key, label) in enumerate(fields, start=1):
            tk.Label(f, text=label, bg=tema.CARD, fg=tema.TEXT,
                     font=(tema.FONT_FAMILY, 10)).grid(
                row=i, column=0, sticky="w", pady=4)
            if key == "jenis_kelamin":
                var = tk.StringVar(value=str(awal.get(key, "Laki-laki")))
                cb = ttk.Combobox(f, textvariable=var, state="readonly",
                                  values=("Laki-laki", "Perempuan"),
                                  font=(tema.FONT_FAMILY, 10), width=24)
                cb.grid(row=i, column=1, pady=4, padx=(12, 0))
                entries[key] = cb  # type: ignore[assignment]
                hasil[key] = var
            else:
                e = tk.Entry(f, font=(tema.FONT_FAMILY, 10), width=26,
                             relief="solid", bd=1,
                             highlightthickness=0,
                             highlightbackground=tema.BORDER)
                e.grid(row=i, column=1, pady=4, padx=(12, 0))
                e.insert(0, str(awal.get(key, "")))
                entries[key] = e

        # Password (hanya saat tambah, opsional saat edit).
        r = len(fields) + 1
        tk.Label(f, text="Password", bg=tema.CARD, fg=tema.TEXT,
                 font=(tema.FONT_FAMILY, 10)).grid(
            row=r, column=0, sticky="w", pady=4)
        pw = tk.Entry(f, show="*", font=(tema.FONT_FAMILY, 10), width=26,
                      relief="solid", bd=1, highlightthickness=0,
                      highlightbackground=tema.BORDER)
        pw.grid(row=r, column=1, pady=4, padx=(12, 0))
        tk.Label(f, text="(kosongkan jika tidak diubah; default: 123456)",
                 bg=tema.CARD, fg=tema.TEXT_MUTED,
                 font=(tema.FONT_FAMILY, 8)).grid(
            row=r + 1, column=0, columnspan=2, sticky="w", pady=(0, 12))

        def simpan() -> None:
            data: dict = {}
            for key, _ in fields:
                if key == "jenis_kelamin":
                    data[key] = hasil[key].get()
                else:
                    data[key] = entries[key].get().strip()
            data["password"] = pw.get()
            for wajib in ("nim", "nama", "username"):
                if not data[wajib]:
                    messagebox.showwarning(
                        "Data belum lengkap", f"Field '{wajib}' wajib diisi.",
                        parent=dlg)
                    return
            hasil.update(data)
            dlg.destroy()

        ttk.Button(f, text="Simpan", style="Primary.TButton",
                   command=simpan).grid(row=r + 2, column=1, sticky="e",
                                         pady=(0, 0), padx=(0, 8))
        ttk.Button(f, text="Batal", style="Secondary.TButton",
                   command=dlg.destroy).grid(row=r + 2, column=0, sticky="e")

        dlg.bind("<Escape>", lambda _e: dlg.destroy())
        self.wait_window(dlg)
        return hasil if "nim" in hasil else None

    def _tambah(self) -> None:
        data = self._form_dialog("Tambah Mahasiswa", {})
        if not data:
            return
        try:
            L.simpan_mahasiswa(data)
            self._muat()
            messagebox.showinfo("Berhasil", "Data mahasiswa ditambahkan.",
                                parent=self)
        except Exception as exc:
            messagebox.showerror("Gagal", str(exc), parent=self)

    def _edit(self) -> None:
        baris = self._tabel.baris_terpilih()
        if not baris:
            messagebox.showinfo("Pilih data", "Pilih mahasiswa yang akan diedit.",
                                parent=self)
            return
        semua = L.ambil_semua_mahasiswa()
        awal = next((m for m in semua if m["nim"] == baris["nim"]), {})
        data = self._form_dialog("Edit Mahasiswa", awal)
        if not data:
            return
        try:
            L.simpan_mahasiswa(data, int(awal["id_mahasiswa"]))
            self._muat()
            messagebox.showinfo("Berhasil", "Data diperbarui.", parent=self)
        except Exception as exc:
            messagebox.showerror("Gagal", str(exc), parent=self)

    def _hapus(self) -> None:
        baris = self._tabel.baris_terpilih()
        if not baris:
            messagebox.showinfo("Pilih data", "Pilih mahasiswa yang akan dihapus.",
                                parent=self)
            return
        if not messagebox.askyesno(
            "Konfirmasi",
            f"Hapus {baris['nama']} ({baris['nim']})?\n"
            "Semua jawaban dan hasil penilaiannya ikut terhapus.",
            parent=self,
        ):
            return
        try:
            semua = L.ambil_semua_mahasiswa()
            target = next(m for m in semua if m["nim"] == baris["nim"])
            L.hapus_mahasiswa(int(target["id_mahasiswa"]))
            self._muat()
        except Exception as exc:
            messagebox.showerror("Gagal", str(exc), parent=self)
