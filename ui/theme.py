"""
Design system: palet, font, metrik, dan style ttk.

Minimalism & Swiss Style — palet biru yang lebih dalam (#1E40AF),
border lebih lembut (#DBEAFE), spacing konsisten 4px base.
Badge kategori risiko tetap semantik: hijau/kuning/merah.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import font as _tkfont
from tkinter import ttk

# ── Warna (Minimalism & Swiss Style) ────────────────────────
PRIMARY: str = "#1E40AF"
PRIMARY_DARK: str = "#1E3A8A"
PRIMARY_LIGHT: str = "#DBEAFE"
PRIMARY_HOVER: str = "#1D4ED8"

SIDEBAR_BG: str = "#0F172A"
SIDEBAR_ACTIVE: str = "#1E40AF"
SIDEBAR_TEXT: str = "#94A3B8"
SIDEBAR_TEXT_ACTIVE: str = "#FFFFFF"

BG: str = "#F8FAFC"
CARD: str = "#FFFFFF"
CARD_BORDER: str = "#E2E8F0"
BORDER: str = "#DBEAFE"

TEXT: str = "#0F172A"
TEXT_SECONDARY: str = "#334155"
TEXT_MUTED: str = "#64748B"
TEXT_HINT: str = "#94A3B8"

WHITE: str = "#FFFFFF"
BLACK: str = "#000000"

DANGER: str = "#DC2626"
DANGER_LIGHT: str = "#FEE2E2"
DANGER_DARK: str = "#B91C1C"

WARNING: str = "#D97706"
WARNING_LIGHT: str = "#FEF3C7"
WARNING_DARK: str = "#B45309"

SUCCESS: str = "#16A34A"
SUCCESS_LIGHT: str = "#DCFCE7"
SUCCESS_DARK: str = "#15803D"

INFO: str = "#2563EB"
INFO_LIGHT: str = "#DBEAFE"

MUTED: str = "#F1F5F9"
MUTED_FOREGROUND: str = "#475569"

# ── Kategori risiko (tetap semantik) ─────────────────────────
KATEGORI_WARNA: dict[str, str] = {
    "Rendah": SUCCESS,
    "Sedang": WARNING,
    "Tinggi": DANGER,
}
KATEGORI_BG: dict[str, str] = {
    "Rendah": SUCCESS_LIGHT,
    "Sedang": WARNING_LIGHT,
    "Tinggi": DANGER_LIGHT,
}

# ── Spacing (4px base) ──────────────────────────────────────
SPACE_XS: int = 4
SPACE_SM: int = 8
SPACE_MD: int = 12
SPACE_BASE: int = 16
SPACE_LG: int = 20
SPACE_XL: int = 24
SPACE_2XL: int = 32
SPACE_3XL: int = 48

# ── Typography ──────────────────────────────────────────────
FONT_FAMILY: str = "Segoe UI"
FONT_FALLBACKS: list[str] = ["Segoe UI", "Helvetica Neue", "Helvetica", "Arial", "TkDefaultFont"]

FONT_PAGE_TITLE = (FONT_FAMILY, 24, "bold")
FONT_SECTION_TITLE = (FONT_FAMILY, 18, "bold")
FONT_CARD_TITLE = (FONT_FAMILY, 14, "bold")
FONT_CARD_VALUE = (FONT_FAMILY, 28, "bold")
FONT_BODY = (FONT_FAMILY, 13)
FONT_BODY_BOLD = (FONT_FAMILY, 13, "bold")
FONT_CAPTION = (FONT_FAMILY, 11)
FONT_CAPTION_BOLD = (FONT_FAMILY, 11, "bold")
FONT_SMALL = (FONT_FAMILY, 10)
FONT_SMALL_BOLD = (FONT_FAMILY, 10, "bold")
FONT_BUTTON = (FONT_FAMILY, 13, "bold")
FONT_BUTTON_SMALL = (FONT_FAMILY, 11, "bold")
FONT_INPUT = (FONT_FAMILY, 13)
FONT_LABEL = (FONT_FAMILY, 13, "bold")
FONT_LABEL_CAPTION = (FONT_FAMILY, 11, "normal")
FONT_TABLE_HEADER = (FONT_FAMILY, 11, "bold")
FONT_TABLE_BODY = (FONT_FAMILY, 12)
FONT_STAT_LABEL = (FONT_FAMILY, 11, "normal")
FONT_STAT_VALUE = (FONT_FAMILY, 28, "bold")
FONT_H1 = FONT_PAGE_TITLE  # legacy alias
FONT_H2 = FONT_SECTION_TITLE
FONT_H3 = FONT_CARD_TITLE
FONT_H4 = (FONT_FAMILY, 12, "bold")
FONT_BODY_RAW = FONT_BODY  # legacy alias

# ── Layout metrik ────────────────────────────────────────────
SIDEBAR_WIDTH: int = 256
HEADER_HEIGHT: int = 64
CARD_PAD: int = 20
CARD_PAD_SM: int = 12
CARD_RADIUS: int = 8
BUTTON_HEIGHT: int = 36
TABLE_ROW_HEIGHT: int = 44
RADIUS: int = 8  # legacy alias

# ── Hovers ───────────────────────────────────────────────────
HOVER_BG: str = "#F1F5F9"
HOVER_DURATION: int = 180  # ms


# ── Helpers ──────────────────────────────────────────────────

def warna_kategori(kategori: str) -> str:
    return KATEGORI_WARNA.get(kategori, TEXT_MUTED)


def bg_kategori(kategori: str) -> str:
    return KATEGORI_BG.get(kategori, MUTED)


def font_berat(base: tuple, ukuran: int) -> tuple:
    return (FONT_FAMILY, ukuran, "bold")


def _deteksi_font() -> str:
    try:
        families = [f.lower() for f in _tkfont.families()]
    except Exception:
        families = []
    for nama in FONT_FALLBACKS:
        if nama.lower() in families:
            return nama
    return "TkDefaultFont"


# ── Konfigurasi ttk ─────────────────────────────────────────

def configure_styles() -> None:
    st = ttk.Style()
    try:
        st.theme_use("clam")
    except Exception:
        pass
    F = _deteksi_font()

    st.configure("TFrame", background=BG)
    st.configure("Card.TFrame", background=CARD)
    st.configure("Sidebar.TFrame", background=SIDEBAR_BG)

    st.configure("TLabel", background=BG, foreground=TEXT, font=(F, 13))
    st.configure("Title.TLabel", font=FONT_PAGE_TITLE, background=BG, foreground=TEXT)
    st.configure("Subtitle.TLabel", font=FONT_SECTION_TITLE, background=BG, foreground=TEXT)
    st.configure("Card.TLabel", background=CARD, foreground=TEXT, font=(F, 13))
    st.configure("CardTitle.TLabel", background=CARD, foreground=TEXT_MUTED,
                 font=FONT_STAT_LABEL)
    st.configure("CardValue.TLabel", background=CARD, foreground=TEXT, font=FONT_STAT_VALUE)
    st.configure("Sidebar.TLabel", background=SIDEBAR_BG, foreground=SIDEBAR_TEXT,
                 font=(F, 13))
    st.configure("SidebarTitle.TLabel", background=SIDEBAR_BG, foreground=WHITE,
                 font=FONT_CARD_TITLE)

    # Primary button — deeper blue, taller
    st.configure("Primary.TButton",
                 background=PRIMARY, foreground=WHITE,
                 font=FONT_BUTTON, padding=(20, 8))
    st.map("Primary.TButton",
           background=[("active", PRIMARY_HOVER), ("pressed", PRIMARY_DARK)])

    # Secondary button — border style
    st.configure("Secondary.TButton",
                 background=WHITE, foreground=TEXT_SECONDARY,
                 font=FONT_BUTTON_SMALL, padding=(16, 6),
                 relief="solid", borderwidth=1)
    st.map("Secondary.TButton",
           background=[("active", HOVER_BG), ("pressed", MUTED)],
           borderwidth=[("pressed", 2)])

    # Danger button
    st.configure("Danger.TButton",
                 background=DANGER, foreground=WHITE,
                 font=FONT_BUTTON, padding=(20, 8))
    st.map("Danger.TButton",
           background=[("active", DANGER_DARK)])

    # Ghost button
    st.configure("Ghost.TButton",
                 background=CARD, foreground=PRIMARY,
                 font=FONT_BUTTON_SMALL, padding=(16, 6))
    st.map("Ghost.TButton",
           background=[("active", PRIMARY_LIGHT)])

    # Treeview — zebra stripes, deeper header, better row height
    st.configure("Treeview",
                 background=WHITE, foreground=TEXT_SECONDARY,
                 rowheight=TABLE_ROW_HEIGHT,
                 font=FONT_TABLE_BODY,
                 fieldbackground=WHITE)
    st.configure("Treeview.Heading",
                 background=PRIMARY, foreground=WHITE,
                 font=FONT_TABLE_HEADER, relief="flat")
    st.map("Treeview",
           background=[("selected", PRIMARY_LIGHT)],
           foreground=[("selected", PRIMARY_DARK)])
    st.map("Treeview.Heading",
           background=[("active", PRIMARY_HOVER)])

    # Entry — taller, cleaner border
    st.configure("TEntry",
                 padding=(10, 8),
                 font=FONT_INPUT)

    # Combobox
    st.configure("TCombobox",
                 padding=(10, 6),
                 font=FONT_BODY)

    # Notebook
    st.configure("TNotebook", background=BG)
    st.configure("TNotebook.Tab",
                 padding=(20, 8),
                 font=FONT_BODY)
    st.map("TNotebook.Tab",
           background=[("selected", WHITE)],
           foreground=[("selected", PRIMARY)])

    # Radiobutton
    st.configure("TRadiobutton",
                 background=BG,
                 font=FONT_BODY)


def terapkan_tema(root: tk.Misc) -> None:
    configure_styles()
    root.configure(bg=BG)
