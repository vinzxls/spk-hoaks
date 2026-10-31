"""Jendela login — pintu masuk satu layar penuh."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox
from typing import Callable

import config
import ui.theme as tema
from core.auth import Aktor, UserSession, authenticate, set_session, clear_session


class LoginFrame(tk.Frame):
    """Frame login dengan role toggle Admin/Mahasiswa."""

    def __init__(
        self,
        parent: tk.Misc,
        *,
        on_login: Callable[[UserSession], None],
    ) -> None:
        super().__init__(parent, bg=tema.BG)
        self._on_login = on_login
        self._role: Aktor = "admin"

        # Tengah layar — card login.
        card = tk.Frame(self, bg=tema.CARD, highlightbackground=tema.BORDER,
                        highlightthickness=1, padx=48, pady=40)
        card.place(relx=0.5, rely=0.5, anchor="center")

        # Judul.
        tk.Label(card, text=config.APP_TITLE, bg=tema.CARD, fg=tema.TEXT,
                 font=(tema.FONT_FAMILY, 14, "bold"),
                 wraplength=280).pack(pady=(0, 4))
        tk.Label(card, text=config.APP_ORG, bg=tema.CARD, fg=tema.TEXT_MUTED,
                 font=(tema.FONT_FAMILY, 9)).pack(pady=(0, 28))

        # Role toggle.
        role_frame = tk.Frame(card, bg=tema.CARD)
        role_frame.pack(fill="x", pady=(0, 16))
        self._role_var = tk.StringVar(value="admin")
        for val, label in [("admin", "Admin"), ("mahasiswa", "Mahasiswa")]:
            tk.Radiobutton(
                role_frame, text=label, variable=self._role_var, value=val,
                bg=tema.CARD, fg=tema.TEXT, selectcolor=tema.WHITE,
                activebackground=tema.CARD,
                font=(tema.FONT_FAMILY, 10),
                command=self._ubah_role,
            ).pack(side="left", padx=12)

        # Form fields.
        self._err = tk.Label(card, text="", bg=tema.CARD, fg=tema.DANGER,
                             font=(tema.FONT_FAMILY, 9), wraplength=260)

        f = tk.Frame(card, bg=tema.CARD)
        f.pack(fill="x")
        tk.Label(f, text="Username", bg=tema.CARD, fg=tema.TEXT,
                 font=(tema.FONT_FAMILY, 10)).pack(anchor="w")
        self._user = tk.Entry(f, font=(tema.FONT_FAMILY, 11),
                              relief="solid", bd=1, highlightthickness=0,
                              highlightbackground=tema.BORDER)
        self._user.pack(fill="x", ipady=7, pady=(2, 10))
        self._user.focus_set()

        tk.Label(f, text="Password", bg=tema.CARD, fg=tema.TEXT,
                 font=(tema.FONT_FAMILY, 10)).pack(anchor="w")
        self._pass = tk.Entry(f, show="*", font=(tema.FONT_FAMILY, 11),
                              relief="solid", bd=1, highlightthickness=0,
                              highlightbackground=tema.BORDER)
        self._pass.pack(fill="x", ipady=7, pady=(2, 20))

        tk.Button(card, text="Login", bg=tema.PRIMARY, fg=tema.WHITE,
                  font=(tema.FONT_FAMILY, 11, "bold"), relief="flat",
                  cursor="hand2", command=self._login,
                  activebackground=tema.PRIMARY_DARK, activeforeground=tema.WHITE,
                  padx=12, pady=8).pack(fill="x")

        self._err.pack(pady=(12, 0))

        # Enter memicu login. Bind HANYA di widget milik frame ini
        # (bind_all akan tetap aktif setelah frame dihancurkan dan
        # memanggil _login pada Entry yang sudah tidak ada -> TclError).
        for w in (self._user, self._pass):
            w.bind("<Return>", self._login)
        for w in role_frame.winfo_children():
            w.bind("<Return>", self._login)

    def _ubah_role(self) -> None:
        self._role = str(self._role_var.get())  # type: ignore[arg-type]

    def _login(self, _event: object = None) -> None:
        # Abaikan Enter yang datang setelah frame ini dihancurkan.
        if not self.winfo_exists():
            return
        try:
            uname = self._user.get().strip()
            pwd = self._pass.get()
        except tk.TclError:  # widget sudah dimusnahkan
            return
        if not uname or not pwd:
            self._tampilkan_err("Username dan password harus diisi.")
            return
        try:
            user = authenticate(uname, pwd, self._role)
        except Exception as exc:
            self._tampilkan_err(
                f"Tidak dapat terhubung ke database: {exc}"
            )
            return
        if user is None:
            # Sebutkan peran yang dipilih: akun admin tidak akan lolos bila
            # toggle masih di "Mahasiswa", dan pesan generik membuat
            # pengguna mengira passwordnya salah.
            self._tampilkan_err(
                "Username atau password salah untuk peran "
                f"'{self._role}'."
            )
            return
        set_session(user)
        self._on_login(user)

    def _tampilkan_err(self, msg: str) -> None:
        self._err.config(text=msg)
