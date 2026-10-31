"""
Komponen UI reusable.

Semua halaman dibangun dari komponen di file ini. Widget hanya
menampilkan data yang sudah di-fetch halaman; tidak ada logika bisnis
maupun query database di sini.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Mapping, Sequence

import ui.theme as tema


def _kartu(parent: tk.Misc, **kw: Any) -> tk.Frame:
    """Frame dengan permukaan kartu: bg putih + border tipis."""
    return tk.Frame(
        parent, bg=tema.CARD,
        highlightbackground=tema.CARD_BORDER, highlightthickness=1, **kw
    )


class StatCard(tk.Frame):
    """Kartu statistik: label kecil, angka besar, delta opsional."""

    def __init__(
        self,
        parent: tk.Misc,
        *,
        label: str,
        value: str,
        accent: str = tema.PRIMARY,
        sub: str = "",
    ) -> None:
        super().__init__(
            parent, bg=tema.CARD,
            highlightbackground=tema.CARD_BORDER, highlightthickness=1,
            cursor="arrow",
        )
        self.accent = accent

        # Aksen tipis di sisi atas kartu.
        tk.Frame(self, bg=accent, height=3, highlightthickness=0).pack(
            fill="x")

        isi = tk.Frame(self, bg=tema.CARD)
        isi.pack(side="left", fill="both", expand=True,
                 padx=tema.SPACE_LG, pady=tema.SPACE_BASE)

        tk.Label(
            isi, text=label.upper(), bg=tema.CARD,
            fg=tema.TEXT_MUTED, font=tema.FONT_STAT_LABEL,
        ).pack(anchor="w")

        self.value_label = tk.Label(
            isi, text=value, bg=tema.CARD, fg=tema.TEXT,
            font=tema.FONT_STAT_VALUE,
        )
        self.value_label.pack(anchor="w", pady=(tema.SPACE_XS, 0))

        if sub:
            tk.Label(
                isi, text=sub, bg=tema.CARD, fg=tema.TEXT_HINT,
                font=tema.FONT_SMALL,
            ).pack(anchor="w", pady=(tema.SPACE_XS, 0))

    def set_value(self, teks: str) -> None:
        self.value_label.config(text=teks)


class KategoriBadge(tk.Label):
    """Pill berwarna untuk kategori risiko (Rendah/Sedang/Tinggi)."""

    def __init__(self, parent: tk.Misc, kategori: str) -> None:
        super().__init__(
            parent, text=kategori,
            bg=tema.bg_kategori(kategori), fg=tema.warna_kategori(kategori),
            font=tema.FONT_SMALL_BOLD, padx=tema.SPACE_MD, pady=3,
        )


class DataTable(tk.Frame):
    """Tabel data ttk.Treeview dengan header, zebra, hover, dan state kosong."""

    def __init__(
        self,
        parent: tk.Misc,
        *,
        kolom: Sequence[tuple[str, str]],
        lebar_min: int = 90,
        on_klik: Callable[[dict[str, str]], None] | None = None,
    ) -> None:
        super().__init__(parent, bg=tema.BG)
        self._kolom = list(kolom)
        self._on_klik = on_klik
        self._pesan: str | None = None

        self.tree = ttk.Treeview(
            self,
            columns=[k for k, _ in kolom],
            show="headings", selectmode="browse",
        )
        for key, judul in kolom:
            self.tree.heading(key, text=judul, anchor="w")
            self.tree.column(key, width=lebar_min, anchor="w",
                             stretch=True, minwidth=lebar_min)

        scrollbar = ttk.Scrollbar(self, orient="vertical",
                                  command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Zebra: baris genap sedikit lebih gelap.
        self.tree.tag_configure("odd", background=tema.CARD)
        self.tree.tag_configure("even", background=tema.MUTED)
        self.tree.tag_configure("hover", background=tema.PRIMARY_LIGHT)

        if on_klik is not None:
            self.tree.bind("<<TreeviewSelect>>", self._handle_klik)
        self._bind_hover()

    def _bind_hover(self) -> None:
        """Sorot baris saat kursor lewat (feedback visual interaktif)."""
        self._hover_iid: str | None = None

        def on_motion(event: Any) -> None:
            if self._pesan is not None:
                return
            baris = self.tree.identify_row(event.y)
            if baris == self._hover_iid:
                return
            self._hover_iid = baris
            for item in self.tree.get_children():
                tags = self.tree.item(item, "tags")
                if tags and str(tags[0]).startswith("k_"):
                    continue
                dasar = "even" if self.tree.index(item) % 2 else "odd"
                self.tree.item(item, tags=(dasar,))
            if baris:
                self.tree.item(baris, tags=("hover",))

        def on_leave(_event: Any) -> None:
            self._hover_iid = None
            for item in self.tree.get_children():
                tags = self.tree.item(item, "tags")
                if tags and str(tags[0]).startswith("k_"):
                    continue
                dasar = "even" if self.tree.index(item) % 2 else "odd"
                self.tree.item(item, tags=(dasar,))

        self.tree.bind("<Motion>", on_motion)
        self.tree.bind("<Leave>", on_leave)

    def _handle_klik(self, _event: Any) -> None:
        if self._pesan is not None:
            return
        baris = self.baris_terpilih()
        if baris is not None and self._on_klik is not None:
            self._on_klik(baris)

    def isi(self, data: Sequence[Mapping[str, Any]]) -> None:
        self.bersihkan()
        for i, item in enumerate(data):
            self.tree.insert(
                "", "end",
                values=[("" if item.get(k) is None else str(item.get(k)))
                        for k, _ in self._kolom],
                tags=("even" if i % 2 else "odd",),
            )

    def bersihkan(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._pesan = None
        self._hover_iid = None

    def baris_terpilih(self) -> dict[str, str] | None:
        if self._pesan is not None:
            return None
        sel = self.tree.selection()
        if not sel:
            return None
        nilai = self.tree.item(sel[0], "values")
        return dict(zip((k for k, _ in self._kolom), nilai))

    def _tampilkan_pesan(self, teks: str) -> None:
        self.bersihkan()
        self._pesan = teks
        self.tree.insert("", "end",
                         values=[teks] + [""] * (len(self._kolom) - 1))

    def set_loading(self, teks: str = "Memuat data...") -> None:
        self._tampilkan_pesan(teks)

    def set_kosong(self, teks: str = "Belum ada data.") -> None:
        self._tampilkan_pesan(teks)


class SearchBox(tk.Frame):
    """Kotak pencarian dengan placeholder dan debounce ~350ms."""

    def __init__(
        self,
        parent: tk.Misc,
        *,
        placeholder: str = "Cari...",
        on_cari: Callable[[str], None] | None = None,
        lebar: int = 280,
    ) -> None:
        super().__init__(parent, bg=tema.BG)
        self._on_cari = on_cari
        self._after_id: str | None = None
        self._placeholder = placeholder

        self.var = tk.StringVar()
        entry = tk.Entry(
            self, textvariable=self.var, width=lebar // 8,
            bg=tema.CARD, fg=tema.TEXT_MUTED,
            relief="flat", bd=0,
            highlightbackground=tema.CARD_BORDER, highlightthickness=1,
            font=tema.FONT_INPUT,
        )
        entry.pack(side="left", ipady=tema.SPACE_SM)
        self.var.set(placeholder)
        self._entry = entry

        def on_focus_in(_e: Any) -> None:
            if self._is_placeholder():
                entry.delete(0, "end")
                entry.configure(fg=tema.TEXT,
                                highlightbackground=tema.PRIMARY)

        def on_focus_out(_e: Any) -> None:
            entry.configure(highlightbackground=tema.CARD_BORDER)
            if not entry.get().strip():
                entry.delete(0, "end")
                self.var.set(placeholder)
                entry.configure(fg=tema.TEXT_MUTED)

        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)
        entry.bind("<KeyRelease>", self._debounce)

    def _is_placeholder(self) -> bool:
        return self.var.get().strip() == self._placeholder

    def _debounce(self, _event: Any = None) -> None:
        if self._after_id is not None:
            self.after_cancel(self._after_id)
        self._after_id = self.after(350, self._jalankan)

    def _jalankan(self) -> None:
        self._after_id = None
        if self._on_cari is not None:
            self._on_cari(self.get())

    def get(self) -> str:
        teks = self.var.get().strip()
        return "" if teks == self._placeholder else teks

    def clear(self) -> None:
        self.var.set(self._placeholder)
        self._entry.configure(fg=tema.TEXT_MUTED)


class DonutChart(tk.Canvas):
    """Diagram donat distribusi kategori risiko."""

    def __init__(
        self,
        parent: tk.Misc,
        *,
        ukuran: int = 220,
        tebal: int = 42,
        bg: str = tema.CARD,
    ) -> None:
        super().__init__(parent, width=ukuran, height=ukuran, bg=bg,
                         highlightthickness=0)
        self._ukuran = ukuran
        self._tebal = tebal
        self._bg = bg

    def gambar(
        self,
        data: Mapping[str, float],
        warna: Mapping[str, str],
        *,
        judul: str = "Total",
    ) -> None:
        self.delete("all")
        s = self._ukuran
        pad = self._tebal // 2 + 4
        bbox = (pad, pad, s - pad, s - pad)
        total = sum(data.values())

        if total <= 0:
            self.create_oval(bbox, outline=tema.CARD_BORDER,
                             width=self._tebal)
            self.create_text(s / 2, s / 2, text="Belum ada data",
                             fill=tema.TEXT_MUTED, font=tema.FONT_CAPTION)
            return

        start = 90.0
        for label, nilai in data.items():
            if nilai <= 0:
                continue
            extent = -360.0 * nilai / total
            self.create_arc(
                bbox, start=start, extent=extent,
                fill=warna.get(label, tema.TEXT_MUTED),
                outline=self._bg, width=2,
            )
            start += extent

        inset = self._tebal
        self.create_oval(
            (pad + inset, pad + inset, s - pad - inset, s - pad - inset),
            fill=self._bg, outline="",
        )
        self.create_text(s / 2, s / 2 - 8, text=f"{int(total)}",
                         fill=tema.TEXT, font=tema.FONT_CARD_VALUE)
        self.create_text(s / 2, s / 2 + 18, text=judul,
                         fill=tema.TEXT_MUTED, font=tema.FONT_CAPTION)


class Legend(tk.Frame):
    """Legenda donat: swatch + label + jumlah + persentase."""

    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent, bg=tema.CARD)

    def isi(self, data: Mapping[str, float], warna: Mapping[str, str]) -> None:
        for child in self.winfo_children():
            child.destroy()
        total = sum(data.values()) or 1.0
        for label, nilai in data.items():
            baris = tk.Frame(self, bg=tema.CARD)
            baris.pack(anchor="w", pady=tema.SPACE_XS)
            tk.Frame(baris, bg=warna.get(label, tema.TEXT_MUTED),
                     width=10, height=10).pack(side="left", pady=2,
                                               padx=(0, tema.SPACE_SM))
            tk.Label(baris, text=label, bg=tema.CARD, fg=tema.TEXT_SECONDARY,
                     font=tema.FONT_BODY, width=8, anchor="w").pack(side="left")
            tk.Label(baris, text=f"{int(nilai)}", bg=tema.CARD, fg=tema.TEXT,
                     font=tema.FONT_BODY_BOLD, width=4, anchor="e").pack(side="left")
            tk.Label(baris, text=f"({nilai / total * 100:.0f}%)",
                     bg=tema.CARD, fg=tema.TEXT_MUTED,
                     font=tema.FONT_CAPTION).pack(side="left", padx=(tema.SPACE_XS, 0))


class Sidebar(tk.Frame):
    """Rel navigasi dengan aksen aktif."""

    def __init__(
        self,
        parent: tk.Misc,
        *,
        menu: Sequence[tuple[str, str]],
        judul: str = "",
        on_pilih: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(parent, bg=tema.SIDEBAR_BG,
                         width=tema.SIDEBAR_WIDTH)
        self.pack_propagate(False)
        self._menu = list(menu)
        self._on_pilih = on_pilih
        self._item: dict[str, tk.Frame] = {}
        self._label: dict[str, tk.Label] = {}
        self._aksen: dict[str, tk.Frame] = {}
        self._aktif: str = ""

        if judul:
            wrap_judul = tk.Frame(self, bg=tema.SIDEBAR_BG)
            wrap_judul.pack(fill="x", padx=tema.SPACE_XL,
                            pady=(tema.SPACE_XL, tema.SPACE_BASE))
            tk.Label(wrap_judul, text=judul, bg=tema.SIDEBAR_BG,
                     fg=tema.WHITE, font=tema.FONT_CARD_TITLE,
                     wraplength=tema.SIDEBAR_WIDTH - 60,
                     justify="left").pack(anchor="w")
            tk.Frame(self, bg=tema.SIDEBAR_ACTIVE, height=2,
                     width=40).pack(anchor="w", padx=tema.SPACE_XL,
                                    pady=(0, tema.SPACE_XL))

        for key, label in self._menu:
            if key == "logout":
                tk.Frame(self, bg=tema.SIDEBAR_BG, height=1).pack(
                    fill="x", padx=tema.SPACE_XL, pady=tema.SPACE_MD)
            baris = self._buat_item(key, label)
            self._item[key] = baris
            baris.pack(fill="x")

        tk.Frame(self, bg=tema.SIDEBAR_BG).pack(side="bottom",
                                                fill="both", expand=True)

    def _buat_item(self, key: str, label: str) -> tk.Frame:
        wrap = tk.Frame(self, bg=tema.SIDEBAR_BG, cursor="hand2")
        aksen = tk.Frame(wrap, bg=tema.SIDEBAR_BG, width=3)
        aksen.pack(side="left", fill="y")
        self._aksen[key] = aksen
        lbl = tk.Label(wrap, text=label, bg=tema.SIDEBAR_BG,
                       fg=tema.SIDEBAR_TEXT, font=tema.FONT_BODY,
                       anchor="w", padx=tema.SPACE_MD, pady=tema.SPACE_MD)
        lbl.pack(side="left", fill="x", expand=True)
        self._label[key] = lbl

        def klik(_e: Any = None) -> None:
            self.set_aktif(key)
            if self._on_pilih is not None:
                self._on_pilih(key)

        wrap.bind("<Button-1>", klik)
        lbl.bind("<Button-1>", klik)
        lbl.bind("<Enter>", lambda _e: self._hover(key, True))
        lbl.bind("<Leave>", lambda _e: self._hover(key, False))
        return wrap

    def _hover(self, key: str, masuk: bool) -> None:
        if key == self._aktif:
            return
        lbl = self._label[key]
        lbl.config(bg=tema.SIDEBAR_ACTIVE if masuk else tema.SIDEBAR_BG,
                   fg=tema.WHITE if masuk else tema.SIDEBAR_TEXT)
        self._item[key].config(
            bg=tema.SIDEBAR_ACTIVE if masuk else tema.SIDEBAR_BG)

    def set_aktif(self, key: str) -> None:
        self._aktif = key
        for k, wrap in self._item.items():
            on = k == key
            bg = tema.SIDEBAR_ACTIVE if on else tema.SIDEBAR_BG
            wrap.config(bg=bg)
            self._label[k].config(bg=bg,
                                  fg=tema.WHITE if on else tema.SIDEBAR_TEXT)
            self._aksen[k].config(
                bg=tema.WHITE if on else tema.SIDEBAR_BG)


class Header(tk.Frame):
    """Bilah judul di atas area konten."""

    def __init__(
        self,
        parent: tk.Misc,
        *,
        judul: str,
        sub_judul: str = "",
        aksi: Sequence[tuple[str, Callable[[], None]]] = (),
    ) -> None:
        # pack_propagate left ON: tinggi header mengikuti isi, sehingga
        # judul dan tombol tidak terpotong pada font/DPI yang berbeda.
        super().__init__(parent, bg=tema.CARD,
                         highlightbackground=tema.CARD_BORDER,
                         highlightthickness=0)

        kiri = tk.Frame(self, bg=tema.CARD)
        kiri.pack(side="left", padx=tema.SPACE_2XL,
                  pady=tema.SPACE_BASE, fill="y")

        self.judul_label = tk.Label(kiri, text=judul, bg=tema.CARD,
                                    fg=tema.TEXT, font=tema.FONT_SECTION_TITLE,
                                    anchor="w")
        self.judul_label.pack(anchor="w")
        if sub_judul:
            tk.Label(kiri, text=sub_judul, bg=tema.CARD, fg=tema.TEXT_MUTED,
                     font=tema.FONT_CAPTION, anchor="w").pack(anchor="w",
                                                              pady=(2, 0))

        if aksi:
            kanan = tk.Frame(self, bg=tema.CARD)
            kanan.pack(side="right", padx=tema.SPACE_2XL,
                       pady=tema.SPACE_BASE, fill="y")
            for label, cmd in aksi:
                ttk.Button(kanan, text=label, command=cmd,
                           style="Primary.TButton",
                           cursor="hand2").pack(side="left",
                                                padx=(tema.SPACE_SM, 0),
                                                expand=True)
        else:
            tk.Frame(self, bg=tema.CARD).pack(side="right",
                                              padx=tema.SPACE_2XL)

    def set_judul(self, teks: str) -> None:
        self.judul_label.config(text=teks)


def _pasang_roda(widget: tk.Misc) -> None:
    """Pasang scroll mouse wheel pada seluruh isi halaman.

    ``bind_all`` dipakai agar roda bekerja di mana pun kursor berada,
    tetapi binding lama dilepas lebih dulu supaya handler dari halaman
    yang sudah dihancurkan tidak menumpuk di root.
    """
    if not hasattr(widget, "_on_wheel"):
        return
    root = widget.winfo_toplevel()
    for urutan in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
        root.unbind_all(urutan)
        root.bind_all(urutan, widget._on_wheel)


class HalamanBase(tk.Frame):
    """Kerangka halaman: sidebar + header + area konten scrollable."""

    def __init__(
        self,
        parent: tk.Misc,
        *,
        judul: str,
        sub_judul: str = "",
        menu: Sequence[tuple[str, str]] = (),
        on_pilih: Callable[[str], None] | None = None,
        aksi: Sequence[tuple[str, Callable[[], None]]] = (),
    ) -> None:
        super().__init__(parent, bg=tema.BG)
        self.pack(fill="both", expand=True)

        from config import APP_TITLE
        self.sidebar = Sidebar(self, menu=menu, judul=APP_TITLE,
                               on_pilih=on_pilih)
        self.sidebar.pack(side="left", fill="y")

        kanan = tk.Frame(self, bg=tema.BG)
        kanan.pack(side="left", fill="both", expand=True)

        self.header = Header(kanan, judul=judul, sub_judul=sub_judul, aksi=aksi)
        self.header.pack(fill="x")

        holder = tk.Frame(kanan, bg=tema.BG)
        holder.pack(fill="both", expand=True)
        self._canvas = tk.Canvas(holder, bg=tema.BG, highlightthickness=0)
        scroll = ttk.Scrollbar(holder, orient="vertical",
                               command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=scroll.set)
        self._canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        self.konten = tk.Frame(self._canvas, bg=tema.BG)
        self._konten_window = self._canvas.create_window(
            (0, 0), window=self.konten, anchor="nw")
        self.konten.bind("<Configure>", lambda _e: self._canvas.configure(
            scrollregion=self._canvas.bbox("all")))
        self._canvas.bind("<Configure>", lambda e: self._canvas.itemconfigure(
            self._konten_window, width=e.width))
        _pasang_roda(self)

    def _on_wheel(self, event: Any) -> None:
        if not self.winfo_exists():
            return
        delta = getattr(event, "delta", 0)
        nomor = getattr(event, "num", 0)
        if nomor == 4:
            langkah = -1
        elif nomor == 5:
            langkah = 1
        else:
            langkah = -int(delta / 120) or (-1 if delta > 0 else 1)
        self._canvas.yview_scroll(langkah, "units")

    def bersihkan_konten(self) -> None:
        for child in self.konten.winfo_children():
            child.destroy()
