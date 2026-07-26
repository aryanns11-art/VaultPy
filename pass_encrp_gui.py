"""
Password Vault - GUI Frontend
CustomTkinter-based GUI that wraps the existing backend functions.
DO NOT modify any backend logic below the "BACKEND" section marker.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import json
from urllib.parse import urlparse
from getpass import getpass
import secrets
import string
from cryptography.fernet import Fernet
import hashlib
import os
import threading
import time
from datetime import datetime

try:
    import pyperclip
    CLIPBOARD_AVAILABLE = True
except ImportError:
    CLIPBOARD_AVAILABLE = False

# ─────────────────────────────────────────────────────────────────────────────
# BACKEND  (unchanged from original — only terminal I/O is replaced by GUI)
# ─────────────────────────────────────────────────────────────────────────────

FILE_NAME = "vault.json"


def load_data():
    try:
        with open(FILE_NAME, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_data(vault):
    with open(FILE_NAME, "w") as file:
        json.dump(vault, file, indent=4)


def valid_url(url):
    result = urlparse(url)
    return all([result.scheme, result.netloc])


def load_key():
    if not os.path.exists("key.key"):
        key = Fernet.generate_key()
        with open("key.key", "wb") as file:
            file.write(key)
        return key
    with open("key.key", "rb") as file:
        return file.read()


key = load_key()
cipher = Fernet(key)


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def setup_master_password(password):
    """GUI-adapted: receives password string directly instead of getpass()."""
    hashed = hash_password(password)
    with open("master.key", "w") as f:
        f.write(hashed)


def check_password_strength(password):
    length = len(password)
    has_lower  = any(c.islower()  for c in password)
    has_upper  = any(c.isupper()  for c in password)
    has_digit  = any(c.isdigit()  for c in password)
    has_symbol = any(c in "!@#$%^&*" for c in password)
    score = sum([has_lower, has_upper, has_digit, has_symbol])
    if length >= 12 and score == 4:
        return "Strong"
    elif length >= 8 and score >= 3:
        return "Medium"
    else:
        return "Weak"


def generate_password(length=16, use_upper=True, use_lower=True,
                       use_digits=True, use_symbols=True):
    """Extended version: supports length and character-set parameters."""
    chars = ""
    if use_lower:   chars += string.ascii_lowercase
    if use_upper:   chars += string.ascii_uppercase
    if use_digits:  chars += string.digits
    if use_symbols: chars += "!@#$%^&*"
    if not chars:
        chars = string.ascii_letters + string.digits
    for _ in range(200):
        password = ''.join(secrets.choice(chars) for _ in range(length))
        ok = True
        if use_lower   and not any(c.islower()  for c in password): ok = False
        if use_upper   and not any(c.isupper()  for c in password): ok = False
        if use_digits  and not any(c.isdigit()  for c in password): ok = False
        if use_symbols and not any(c in "!@#$%^&*" for c in password): ok = False
        if ok:
            return password
    return password  # fallback


def verify_master_password(password):
    """Returns True if password matches stored hash."""
    if not os.path.exists("master.key"):
        return None  # not yet set
    with open("master.key", "r") as f:
        stored_hash = f.read()
    return hash_password(password) == stored_hash


def decrypt_password(encrypted):
    return cipher.decrypt(encrypted.encode()).decode()


def encrypt_password(plain):
    return cipher.encrypt(plain.encode()).decode()


# ─────────────────────────────────────────────────────────────────────────────
# DESIGN TOKENS
# ─────────────────────────────────────────────────────────────────────────────

PALETTE = {
    "bg":           "#0D0F14",   # near-black background
    "surface":      "#13161E",   # card / sidebar surface
    "surface2":     "#1A1E2A",   # elevated cards
    "border":       "#252A38",   # subtle borders
    "accent":       "#4F8EF7",   # electric blue — primary accent
    "accent_dim":   "#2B4F9E",   # darker accent for hover
    "accent2":      "#7C5CF7",   # violet secondary accent
    "success":      "#27C78A",   # green
    "warning":      "#F7A94F",   # amber
    "danger":       "#F75A5A",   # red
    "text":         "#E8EAF0",   # primary text
    "text_muted":   "#6B7280",   # secondary / placeholder text
    "text_dim":     "#9CA3AF",   # mid-level labels
}

FONT_FAMILY = "Segoe UI" if os.name == "nt" else "SF Pro Display"
FONT_MONO   = "Consolas"  if os.name == "nt" else "Menlo"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


# ─────────────────────────────────────────────────────────────────────────────
# HELPER WIDGETS
# ─────────────────────────────────────────────────────────────────────────────

class IconLabel(ctk.CTkLabel):
    """A label that displays a Unicode emoji/icon + optional text."""
    def __init__(self, master, icon="", text="", icon_size=20, **kw):
        combined = f"{icon}  {text}" if text else icon
        super().__init__(master, text=combined,
                         font=(FONT_FAMILY, icon_size), **kw)


class Card(ctk.CTkFrame):
    """Elevated card with consistent styling."""
    def __init__(self, master, **kw):
        kw.setdefault("fg_color",      PALETTE["surface2"])
        kw.setdefault("corner_radius", 14)
        kw.setdefault("border_width",  1)
        kw.setdefault("border_color",  PALETTE["border"])
        super().__init__(master, **kw)


class PrimaryButton(ctk.CTkButton):
    def __init__(self, master, **kw):
        kw.setdefault("fg_color",          PALETTE["accent"])
        kw.setdefault("hover_color",       PALETTE["accent_dim"])
        kw.setdefault("corner_radius",     10)
        kw.setdefault("font",              (FONT_FAMILY, 13, "bold"))
        kw.setdefault("text_color",        "#FFFFFF")
        kw.setdefault("height",            42)
        super().__init__(master, **kw)


class DangerButton(ctk.CTkButton):
    def __init__(self, master, **kw):
        kw.setdefault("fg_color",      PALETTE["danger"])
        kw.setdefault("hover_color",   "#C0392B")
        kw.setdefault("corner_radius", 10)
        kw.setdefault("font",          (FONT_FAMILY, 13, "bold"))
        kw.setdefault("text_color",    "#FFFFFF")
        kw.setdefault("height",        42)
        super().__init__(master, **kw)


class GhostButton(ctk.CTkButton):
    def __init__(self, master, **kw):
        kw.setdefault("fg_color",      "transparent")
        kw.setdefault("hover_color",   PALETTE["border"])
        kw.setdefault("border_width",  1)
        kw.setdefault("border_color",  PALETTE["border"])
        kw.setdefault("corner_radius", 10)
        kw.setdefault("font",          (FONT_FAMILY, 12))
        kw.setdefault("text_color",    PALETTE["text_dim"])
        kw.setdefault("height",        38)
        super().__init__(master, **kw)


class FormEntry(ctk.CTkEntry):
    def __init__(self, master, **kw):
        kw.setdefault("fg_color",       PALETTE["surface"])
        kw.setdefault("border_color",   PALETTE["border"])
        kw.setdefault("border_width",   1)
        kw.setdefault("corner_radius",  10)
        kw.setdefault("font",           (FONT_FAMILY, 13))
        kw.setdefault("text_color",     PALETTE["text"])
        kw.setdefault("height",         44)
        super().__init__(master, **kw)


class SectionTitle(ctk.CTkLabel):
    def __init__(self, master, text, **kw):
        kw.setdefault("font",       (FONT_FAMILY, 22, "bold"))
        kw.setdefault("text_color", PALETTE["text"])
        super().__init__(master, text=text, **kw)


class FieldLabel(ctk.CTkLabel):
    def __init__(self, master, text, **kw):
        kw.setdefault("font",       (FONT_FAMILY, 12))
        kw.setdefault("text_color", PALETTE["text_dim"])
        super().__init__(master, text=text, **kw)


def copy_to_clipboard(text, app):
    """Copy text to clipboard and show a brief toast."""
    if CLIPBOARD_AVAILABLE:
        pyperclip.copy(text)
    else:
        app.clipboard_clear()
        app.clipboard_append(text)
    app.show_toast("✅  Copied to clipboard!")


# ─────────────────────────────────────────────────────────────────────────────
# TOAST / NOTIFICATION
# ─────────────────────────────────────────────────────────────────────────────

class Toast(ctk.CTkToplevel):
    def __init__(self, parent, message, kind="success", duration=2200):
        super().__init__(parent)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        colors = {
            "success": (PALETTE["success"], "#0D2B20"),
            "error":   (PALETTE["danger"],  "#2B0D0D"),
            "info":    (PALETTE["accent"],  "#0D1A2B"),
        }
        fg, bg = colors.get(kind, colors["info"])
        self.configure(fg_color=bg)
        lbl = ctk.CTkLabel(self, text=message,
                            font=(FONT_FAMILY, 13, "bold"),
                            text_color=fg,
                            fg_color=bg,
                            corner_radius=10,
                            padx=20, pady=12)
        lbl.pack()
        self.update_idletasks()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        px, py = parent.winfo_rootx(), parent.winfo_rooty()
        tw, th = self.winfo_width(), self.winfo_height()
        x = px + (pw - tw) // 2
        y = py + ph - th - 40
        self.geometry(f"+{x}+{y}")
        self.after(duration, self.destroy)


# ─────────────────────────────────────────────────────────────────────────────
# CONFIRM DIALOG
# ─────────────────────────────────────────────────────────────────────────────

class ConfirmDialog(ctk.CTkToplevel):
    def __init__(self, parent, title, message, on_confirm):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.configure(fg_color=PALETTE["surface"])
        self.grab_set()
        self.result = False

        self.geometry("420x200")
        self.update_idletasks()
        pw = parent.winfo_rootx() + (parent.winfo_width()  - 420) // 2
        ph = parent.winfo_rooty() + (parent.winfo_height() - 200) // 2
        self.geometry(f"420x200+{pw}+{ph}")

        ctk.CTkLabel(self, text=title, font=(FONT_FAMILY, 16, "bold"),
                     text_color=PALETTE["danger"]).pack(pady=(24, 4))
        ctk.CTkLabel(self, text=message, font=(FONT_FAMILY, 13),
                     text_color=PALETTE["text_dim"],
                     wraplength=360).pack(pady=(0, 20))

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack()

        def _cancel():
            self.destroy()

        def _confirm():
            self.destroy()
            on_confirm()

        GhostButton(btn_frame, text="Cancel", width=140, command=_cancel).pack(side="left", padx=8)
        DangerButton(btn_frame, text="Delete", width=140, command=_confirm).pack(side="left", padx=8)


# ─────────────────────────────────────────────────────────────────────────────
# LOGIN WINDOW
# ─────────────────────────────────────────────────────────────────────────────

class LoginWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Password Vault")
        self.geometry("480x620")
        self.resizable(False, False)
        self.configure(fg_color=PALETTE["bg"])
        self._attempts = 0
        self._max_attempts = 3
        self._build_ui()
        self.bind("<Return>", lambda e: self._login())

    def _build_ui(self):
        # ── Outer centering frame
        outer = ctk.CTkFrame(self, fg_color="transparent")
        outer.place(relx=0.5, rely=0.5, anchor="center")

        # ── Shield logo
        logo_frame = ctk.CTkFrame(outer,
                                   fg_color=PALETTE["surface2"],
                                   corner_radius=24,
                                   width=90, height=90)
        logo_frame.pack(pady=(0, 18))
        logo_frame.pack_propagate(False)
        ctk.CTkLabel(logo_frame, text="🔐",
                     font=(FONT_FAMILY, 42),
                     fg_color="transparent").place(relx=0.5, rely=0.5, anchor="center")

        # ── Title
        ctk.CTkLabel(outer, text="Password Vault",
                     font=(FONT_FAMILY, 28, "bold"),
                     text_color=PALETTE["text"]).pack()
        ctk.CTkLabel(outer, text="Secure. Private. Yours.",
                     font=(FONT_FAMILY, 13),
                     text_color=PALETTE["text_muted"]).pack(pady=(2, 28))

        # ── Card
        card = Card(outer, width=360)
        card.pack(padx=10, ipadx=10, ipady=24)

        FieldLabel(card, text="MASTER PASSWORD").pack(anchor="w", padx=24, pady=(20, 6))

        pw_row = ctk.CTkFrame(card, fg_color="transparent")
        pw_row.pack(padx=24, fill="x")

        self._pw_var = ctk.StringVar()
        self._pw_entry = FormEntry(pw_row, textvariable=self._pw_var,
                                    show="●", width=280)
        self._pw_entry.pack(side="left", fill="x", expand=True)
        self._pw_entry.focus()

        self._show_var = ctk.BooleanVar(value=False)
        ctk.CTkButton(pw_row, text="👁", width=44, height=44,
                      fg_color=PALETTE["surface"],
                      hover_color=PALETTE["border"],
                      corner_radius=10,
                      command=self._toggle_show).pack(side="left", padx=(8, 0))

        # Attempts label
        self._attempts_lbl = ctk.CTkLabel(card, text="",
                                           font=(FONT_FAMILY, 12),
                                           text_color=PALETTE["danger"])
        self._attempts_lbl.pack(pady=(8, 0))

        PrimaryButton(card, text="🔓  Unlock Vault",
                      width=312,
                      command=self._login).pack(pady=(16, 8))

        GhostButton(card, text="✕  Exit",
                    width=312,
                    command=self.destroy).pack(pady=(0, 20))

        # ── Footer
        ctk.CTkLabel(outer, text="v1.0  •  AES-256 Encrypted",
                     font=(FONT_FAMILY, 11),
                     text_color=PALETTE["text_muted"]).pack(pady=(16, 0))

    def _toggle_show(self):
        self._show_var.set(not self._show_var.get())
        self._pw_entry.configure(show="" if self._show_var.get() else "●")

    def _login(self):
        pw = self._pw_var.get().strip()
        if not pw:
            self._attempts_lbl.configure(text="Password cannot be empty.")
            return

        # First-time setup
        if not os.path.exists("master.key"):
            setup_master_password(pw)
            self._launch_dashboard()
            return

        result = verify_master_password(pw)
        if result:
            self._launch_dashboard()
        else:
            self._attempts += 1
            remaining = self._max_attempts - self._attempts
            if remaining <= 0:
                self._attempts_lbl.configure(text="Access denied. Too many attempts.")
                self._pw_entry.configure(state="disabled")
            else:
                self._attempts_lbl.configure(
                    text=f"Incorrect password. {remaining} attempt(s) remaining.")
            self._pw_var.set("")

    def _launch_dashboard(self):
        self.withdraw()
        dash = Dashboard(on_logout=self._on_logout)
        dash.mainloop()

    def _on_logout(self):
        self.deiconify()
        self._pw_var.set("")
        self._attempts = 0
        self._attempts_lbl.configure(text="")
        self._pw_entry.configure(state="normal")
        self._pw_entry.focus()


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR NAV BUTTON
# ─────────────────────────────────────────────────────────────────────────────

class NavButton(ctk.CTkButton):
    def __init__(self, master, icon, label, command, **kw):
        text = f"  {icon}  {label}"
        kw.setdefault("anchor",        "w")
        kw.setdefault("fg_color",      "transparent")
        kw.setdefault("hover_color",   PALETTE["surface2"])
        kw.setdefault("corner_radius", 10)
        kw.setdefault("font",          (FONT_FAMILY, 13))
        kw.setdefault("text_color",    PALETTE["text_dim"])
        kw.setdefault("height",        46)
        super().__init__(master, text=text, command=command, **kw)

    def set_active(self, active: bool):
        if active:
            self.configure(fg_color=PALETTE["surface2"],
                           text_color=PALETTE["accent"],
                           font=(FONT_FAMILY, 13, "bold"))
        else:
            self.configure(fg_color="transparent",
                           text_color=PALETTE["text_dim"],
                           font=(FONT_FAMILY, 13))


# ─────────────────────────────────────────────────────────────────────────────
# MAIN DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────

class Dashboard(ctk.CTkToplevel):
    PAGES = [
        ("🏠", "Dashboard",    "dashboard"),
        ("➕", "Add Password", "add"),
        ("👁", "View All",     "view"),
        ("🔍", "Search",       "search"),
        ("✏️", "Update",       "update"),
        ("🗑", "Delete",       "delete"),
        ("🎲", "Generator",    "generator"),
    ]

    def __init__(self, on_logout=None):
        super().__init__()
        self.title("Password Vault")
        self.geometry("1100x720")
        self.minsize(900, 600)
        self.configure(fg_color=PALETTE["bg"])
        self._on_logout_cb = on_logout
        self._vault = load_data()
        self._current_page = "dashboard"
        self._nav_buttons = {}
        self._content_frame = None
        self._clock_lbl = None

        self._build_layout()
        self._show_page("dashboard")
        self._tick_clock()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── Layout skeleton ────────────────────────────────────────────────────

    def _build_layout(self):
        # Sidebar
        self._sidebar = ctk.CTkFrame(self, width=220,
                                      fg_color=PALETTE["surface"],
                                      corner_radius=0)
        self._sidebar.pack(side="left", fill="y")
        self._sidebar.pack_propagate(False)

        # Right column
        right = ctk.CTkFrame(self, fg_color="transparent")
        right.pack(side="left", fill="both", expand=True)

        # Header
        self._header = ctk.CTkFrame(right, height=64,
                                     fg_color=PALETTE["surface"],
                                     corner_radius=0)
        self._header.pack(fill="x")
        self._header.pack_propagate(False)
        self._build_header()

        # Content area
        self._content_area = ctk.CTkFrame(right, fg_color="transparent")
        self._content_area.pack(fill="both", expand=True, padx=24, pady=20)

        self._build_sidebar()

    def _build_sidebar(self):
        # Brand
        brand = ctk.CTkFrame(self._sidebar, fg_color="transparent", height=80)
        brand.pack(fill="x")
        brand.pack_propagate(False)
        ctk.CTkLabel(brand, text="🔐  Vault",
                     font=(FONT_FAMILY, 19, "bold"),
                     text_color=PALETTE["accent"]).place(relx=0.5, rely=0.5, anchor="center")

        # Divider
        ctk.CTkFrame(self._sidebar, height=1, fg_color=PALETTE["border"]).pack(fill="x", padx=16)

        # Nav items
        nav_frame = ctk.CTkFrame(self._sidebar, fg_color="transparent")
        nav_frame.pack(fill="both", expand=True, padx=10, pady=10)

        for icon, label, key in self.PAGES:
            btn = NavButton(nav_frame, icon, label,
                            command=lambda k=key: self._show_page(k))
            btn.pack(fill="x", pady=2)
            self._nav_buttons[key] = btn

        # Logout at bottom
        ctk.CTkFrame(self._sidebar, height=1, fg_color=PALETTE["border"]).pack(fill="x", padx=16)
        DangerButton(self._sidebar, text="⎋  Logout",
                     fg_color="transparent",
                     hover_color=PALETTE["surface2"],
                     text_color=PALETTE["danger"],
                     border_width=0,
                     height=46,
                     anchor="w",
                     command=self._logout).pack(fill="x", padx=10, pady=12)

    def _build_header(self):
        ctk.CTkLabel(self._header, text="Password Vault",
                     font=(FONT_FAMILY, 15, "bold"),
                     text_color=PALETTE["text"]).pack(side="left", padx=24)

        self._clock_lbl = ctk.CTkLabel(self._header, text="",
                                        font=(FONT_MONO, 12),
                                        text_color=PALETTE["text_muted"])
        self._clock_lbl.pack(side="right", padx=24)

    def _tick_clock(self):
        now = datetime.now().strftime("%a %d %b  %H:%M:%S")
        if self._clock_lbl:
            self._clock_lbl.configure(text=now)
        self.after(1000, self._tick_clock)

    # ── Page routing ───────────────────────────────────────────────────────

    def _show_page(self, key):
        self._current_page = key
        # Update nav highlights
        for k, btn in self._nav_buttons.items():
            btn.set_active(k == key)
        # Clear content
        for w in self._content_area.winfo_children():
            w.destroy()
        # Render
        pages = {
            "dashboard": self._page_dashboard,
            "add":       self._page_add,
            "view":      self._page_view,
            "search":    self._page_search,
            "update":    self._page_update,
            "delete":    self._page_delete,
            "generator": self._page_generator,
        }
        pages.get(key, self._page_dashboard)()

    def _reload_vault(self):
        self._vault = load_data()

    # ── Shared helpers ─────────────────────────────────────────────────────

    def show_toast(self, msg, kind="success"):
        Toast(self, msg, kind=kind)

    def _scrollable(self):
        """Returns a scrollable inner frame filling the content area."""
        sf = ctk.CTkScrollableFrame(self._content_area,
                                     fg_color="transparent",
                                     scrollbar_button_color=PALETTE["border"],
                                     scrollbar_button_hover_color=PALETTE["accent"])
        sf.pack(fill="both", expand=True)
        return sf

    # ─────────────────────────────────────────────────────────────────────
    # PAGE: DASHBOARD
    # ─────────────────────────────────────────────────────────────────────

    def _page_dashboard(self):
        self._reload_vault()
        frame = self._scrollable()
        SectionTitle(frame, text="Dashboard").pack(anchor="w", pady=(0, 20))

        # ── Stat cards row ────────────────────────────────────────────────
        cards_row = ctk.CTkFrame(frame, fg_color="transparent")
        cards_row.pack(fill="x", pady=(0, 20))

        total = len(self._vault)
        weak = sum(1 for v in self._vault.values()
                   if check_password_strength(
                       decrypt_password(v["password"])) == "Weak")
        medium = sum(1 for v in self._vault.values()
                     if check_password_strength(
                         decrypt_password(v["password"])) == "Medium")
        strong = total - weak - medium

        def stat_card(parent, icon, label, value, color):
            c = Card(parent, width=200, height=120)
            c.pack(side="left", padx=(0, 14), ipadx=10, ipady=10)
            c.pack_propagate(False)
            ctk.CTkLabel(c, text=icon, font=(FONT_FAMILY, 28)).place(relx=0.12, rely=0.28)
            ctk.CTkLabel(c, text=str(value),
                         font=(FONT_FAMILY, 32, "bold"),
                         text_color=color).place(relx=0.5, rely=0.32, anchor="n")
            ctk.CTkLabel(c, text=label,
                         font=(FONT_FAMILY, 11),
                         text_color=PALETTE["text_muted"]).place(relx=0.5, rely=0.75, anchor="n")

        stat_card(cards_row, "🔑", "Total Passwords",   total,  PALETTE["accent"])
        stat_card(cards_row, "💪", "Strong",            strong, PALETTE["success"])
        stat_card(cards_row, "⚡", "Medium",            medium, PALETTE["warning"])
        stat_card(cards_row, "⚠️", "Weak",             weak,   PALETTE["danger"])

        # ── Security bar ──────────────────────────────────────────────────
        sec_card = Card(frame)
        sec_card.pack(fill="x", pady=(0, 20), ipady=16, ipadx=20)

        header_row = ctk.CTkFrame(sec_card, fg_color="transparent")
        header_row.pack(fill="x", padx=20, pady=(16, 8))
        ctk.CTkLabel(header_row, text="🛡  Security Health",
                     font=(FONT_FAMILY, 15, "bold"),
                     text_color=PALETTE["text"]).pack(side="left")
        score_pct = int((strong / total * 100) if total else 0)
        color = PALETTE["success"] if score_pct >= 70 else (
            PALETTE["warning"] if score_pct >= 40 else PALETTE["danger"])
        ctk.CTkLabel(header_row, text=f"{score_pct}%",
                     font=(FONT_FAMILY, 15, "bold"),
                     text_color=color).pack(side="right")

        bar_bg = ctk.CTkFrame(sec_card, height=8, corner_radius=4,
                               fg_color=PALETTE["border"])
        bar_bg.pack(fill="x", padx=20, pady=(0, 8))
        if score_pct > 0:
            bar_fill = ctk.CTkFrame(bar_bg, height=8, corner_radius=4,
                                     fg_color=color,
                                     width=int(bar_bg.winfo_reqwidth() * score_pct / 100))
            bar_fill.place(x=0, y=0, relwidth=score_pct / 100, relheight=1)

        ctk.CTkLabel(sec_card,
                     text=f"{strong} strong  ·  {medium} medium  ·  {weak} weak passwords",
                     font=(FONT_FAMILY, 12),
                     text_color=PALETTE["text_muted"]).pack(padx=20, pady=(0, 16))

        # ── Recent entries ────────────────────────────────────────────────
        if self._vault:
            ctk.CTkLabel(frame, text="Recent Entries",
                         font=(FONT_FAMILY, 16, "bold"),
                         text_color=PALETTE["text"]).pack(anchor="w", pady=(0, 10))

            recent = list(self._vault.items())[-5:][::-1]
            for web, data in recent:
                row = Card(frame)
                row.pack(fill="x", pady=4, ipady=6)
                inner = ctk.CTkFrame(row, fg_color="transparent")
                inner.pack(fill="x", padx=16, pady=10)
                ctk.CTkLabel(inner, text="🌐",
                             font=(FONT_FAMILY, 18)).pack(side="left", padx=(0, 12))
                ctk.CTkLabel(inner, text=web.capitalize(),
                             font=(FONT_FAMILY, 14, "bold"),
                             text_color=PALETTE["text"]).pack(side="left")
                ctk.CTkLabel(inner, text=data["username"],
                             font=(FONT_FAMILY, 12),
                             text_color=PALETTE["text_muted"]).pack(side="left", padx=12)
                strength = check_password_strength(decrypt_password(data["password"]))
                s_color = {"Strong": PALETTE["success"],
                           "Medium": PALETTE["warning"],
                           "Weak":   PALETTE["danger"]}[strength]
                ctk.CTkLabel(inner, text=strength,
                             font=(FONT_FAMILY, 11, "bold"),
                             text_color=s_color).pack(side="right")

    # ─────────────────────────────────────────────────────────────────────
    # PAGE: ADD PASSWORD
    # ─────────────────────────────────────────────────────────────────────

    def _page_add(self):
        frame = self._scrollable()
        SectionTitle(frame, text="Add Password").pack(anchor="w", pady=(0, 20))

        card = Card(frame)
        card.pack(fill="x", ipady=10)

        def field(label, placeholder="", show=""):
            FieldLabel(card, text=label).pack(anchor="w", padx=24, pady=(16, 4))
            e = FormEntry(card, placeholder_text=placeholder, show=show, width=500)
            e.pack(padx=24, fill="x")
            return e

        e_site    = field("WEBSITE NAME",  "e.g. google")
        e_url     = field("WEBSITE URL",   "https://google.com")
        e_user    = field("USERNAME / EMAIL", "user@example.com")

        # Password row
        FieldLabel(card, text="PASSWORD").pack(anchor="w", padx=24, pady=(16, 4))
        pw_row = ctk.CTkFrame(card, fg_color="transparent")
        pw_row.pack(padx=24, fill="x")
        e_pass = FormEntry(pw_row, placeholder_text="Enter or generate a password",
                            show="●", width=390)
        e_pass.pack(side="left", fill="x", expand=True)

        show_var = ctk.BooleanVar()
        def toggle_pw():
            show_var.set(not show_var.get())
            e_pass.configure(show="" if show_var.get() else "●")
        ctk.CTkButton(pw_row, text="👁", width=44, height=44,
                      fg_color=PALETTE["surface"],
                      hover_color=PALETTE["border"],
                      corner_radius=10,
                      command=toggle_pw).pack(side="left", padx=6)

        GhostButton(pw_row, text="🎲 Generate",
                    command=lambda: e_pass.insert(0, generate_password()) or
                                    e_pass.delete(0, len(e_pass.get()) - len(generate_password())),
                    width=110).pack(side="left")

        # Strength meter
        strength_lbl = ctk.CTkLabel(card, text="",
                                     font=(FONT_FAMILY, 12),
                                     text_color=PALETTE["text_muted"])
        strength_lbl.pack(anchor="w", padx=24, pady=(4, 0))

        def update_strength(*_):
            pw = e_pass.get()
            if not pw:
                strength_lbl.configure(text="")
                return
            s = check_password_strength(pw)
            c = {"Strong": PALETTE["success"], "Medium": PALETTE["warning"],
                 "Weak": PALETTE["danger"]}[s]
            strength_lbl.configure(text=f"Strength: {s}", text_color=c)

        e_pass.bind("<KeyRelease>", update_strength)

        def _gen_and_fill():
            pw = generate_password()
            e_pass.delete(0, "end")
            e_pass.insert(0, pw)
            update_strength()

        # Re-wire generate button properly
        for w in pw_row.winfo_children():
            if isinstance(w, ctk.CTkButton) and "Generate" in str(w.cget("text")):
                w.configure(command=_gen_and_fill)

        # Buttons
        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(padx=24, pady=20, fill="x")

        def _save():
            site  = e_site.get().strip().lower()
            url   = e_url.get().strip()
            user  = e_user.get().strip()
            pw    = e_pass.get()

            if not all([site, url, user, pw]):
                self.show_toast("⚠️  All fields are required.", kind="error"); return
            if not valid_url(url):
                self.show_toast("⚠️  Invalid URL format.", kind="error"); return
            self._reload_vault()
            if site in self._vault:
                self.show_toast("⚠️  Website already exists.", kind="error"); return
            strength = check_password_strength(pw)
            if strength == "Weak":
                self.show_toast("⚠️  Password too weak — strengthen it.", kind="error"); return

            encrypted = encrypt_password(pw)
            self._vault[site] = {"username": user, "password": encrypted, "url": url}
            save_data(self._vault)
            self.show_toast("✅  Password saved!")
            _clear()

        def _clear():
            for e in [e_site, e_url, e_user, e_pass]:
                e.delete(0, "end")
            strength_lbl.configure(text="")

        PrimaryButton(btn_row, text="💾  Save",  width=180, command=_save).pack(side="left", padx=(0, 12))
        GhostButton(btn_row,   text="✕  Clear", width=120, command=_clear).pack(side="left")

    # ─────────────────────────────────────────────────────────────────────
    # PAGE: VIEW ALL PASSWORDS
    # ─────────────────────────────────────────────────────────────────────

    def _page_view(self):
        self._reload_vault()

        # Header row
        h_row = ctk.CTkFrame(self._content_area, fg_color="transparent")
        h_row.pack(fill="x", pady=(0, 16))
        SectionTitle(h_row, text=f"All Passwords  ({len(self._vault)})").pack(side="left")
        PrimaryButton(h_row, text="⟳  Refresh", width=120,
                      command=lambda: self._show_page("view")).pack(side="right")

        if not self._vault:
            ctk.CTkLabel(self._content_area, text="No passwords stored yet.",
                         font=(FONT_FAMILY, 15),
                         text_color=PALETTE["text_muted"]).pack(pady=60)
            return

        # Table frame
        sf = ctk.CTkScrollableFrame(self._content_area,
                                     fg_color="transparent",
                                     scrollbar_button_color=PALETTE["border"])
        sf.pack(fill="both", expand=True)

        # Column headers
        hdr = ctk.CTkFrame(sf, fg_color=PALETTE["surface2"],
                            corner_radius=10)
        hdr.pack(fill="x", pady=(0, 4))
        for col, w in [("Website", 160), ("Username", 200), ("Password", 180),
                       ("Strength", 90), ("Actions", 200)]:
            ctk.CTkLabel(hdr, text=col, font=(FONT_FAMILY, 12, "bold"),
                         text_color=PALETTE["text_muted"],
                         width=w, anchor="w").pack(side="left", padx=12, pady=10)

        # Rows
        revealed = {}

        def _row(web, data):
            row = ctk.CTkFrame(sf, fg_color=PALETTE["surface"],
                                corner_radius=10, border_width=1,
                                border_color=PALETTE["border"])
            row.pack(fill="x", pady=3)

            enc_pw = data["password"]

            # Website
            ctk.CTkLabel(row, text=f"🌐  {web.capitalize()}",
                         font=(FONT_FAMILY, 13, "bold"),
                         text_color=PALETTE["text"],
                         width=160, anchor="w").pack(side="left", padx=12, pady=12)
            # Username
            ctk.CTkLabel(row, text=data["username"],
                         font=(FONT_FAMILY, 12),
                         text_color=PALETTE["text_dim"],
                         width=200, anchor="w").pack(side="left", padx=12)

            # Password (masked)
            pw_plain = decrypt_password(enc_pw)
            masked   = pw_plain[:2] + "●" * (len(pw_plain) - 2)
            pw_lbl = ctk.CTkLabel(row, text=masked,
                                   font=(FONT_MONO, 12),
                                   text_color=PALETTE["text_dim"],
                                   width=180, anchor="w")
            pw_lbl.pack(side="left", padx=12)
            revealed[web] = False

            # Strength
            s = check_password_strength(pw_plain)
            s_color = {"Strong": PALETTE["success"], "Medium": PALETTE["warning"],
                       "Weak": PALETTE["danger"]}[s]
            ctk.CTkLabel(row, text=s, font=(FONT_FAMILY, 11, "bold"),
                         text_color=s_color, width=90, anchor="w").pack(side="left", padx=12)

            # Actions
            act = ctk.CTkFrame(row, fg_color="transparent", width=200)
            act.pack(side="left", padx=8)

            def _toggle_reveal(w=web, lbl=pw_lbl, plain=pw_plain, msk=masked):
                revealed[w] = not revealed[w]
                lbl.configure(text=plain if revealed[w] else msk)

            def _copy_pw(plain=pw_plain):
                copy_to_clipboard(plain, self)

            def _copy_user(u=data["username"]):
                copy_to_clipboard(u, self)

            GhostButton(act, text="👁", width=38, height=34,
                        command=_toggle_reveal).pack(side="left", padx=2)
            GhostButton(act, text="🔑", width=38, height=34,
                        command=_copy_pw).pack(side="left", padx=2)
            GhostButton(act, text="👤", width=38, height=34,
                        command=_copy_user).pack(side="left", padx=2)

        for web, data in self._vault.items():
            _row(web, data)

    # ─────────────────────────────────────────────────────────────────────
    # PAGE: SEARCH
    # ─────────────────────────────────────────────────────────────────────

    def _page_search(self):
        self._reload_vault()
        frame = self._scrollable()
        SectionTitle(frame, text="Search Passwords").pack(anchor="w", pady=(0, 20))

        card = Card(frame)
        card.pack(fill="x", ipady=8)

        FieldLabel(card, text="WEBSITE NAME").pack(anchor="w", padx=24, pady=(20, 6))
        search_row = ctk.CTkFrame(card, fg_color="transparent")
        search_row.pack(padx=24, fill="x")
        e_search = FormEntry(search_row, placeholder_text="Type to search...", width=400)
        e_search.pack(side="left", fill="x", expand=True)
        e_search.focus()
        PrimaryButton(search_row, text="🔍  Search", width=130,
                      command=lambda: _do_search()).pack(side="left", padx=(12, 0))

        results_frame = ctk.CTkFrame(frame, fg_color="transparent")
        results_frame.pack(fill="x", pady=16)

        def _do_search():
            for w in results_frame.winfo_children():
                w.destroy()
            query = e_search.get().strip().lower()
            if not query:
                return
            matches = [k for k in self._vault if query in k]
            if not matches:
                ctk.CTkLabel(results_frame, text="No matching websites found.",
                             font=(FONT_FAMILY, 13),
                             text_color=PALETTE["text_muted"]).pack(pady=20)
                return

            ctk.CTkLabel(results_frame,
                         text=f"{len(matches)} result(s) found",
                         font=(FONT_FAMILY, 12),
                         text_color=PALETTE["text_muted"]).pack(anchor="w", pady=(0, 10))

            for web in matches:
                data = self._vault[web]
                pw   = decrypt_password(data["password"])
                s    = check_password_strength(pw)

                rc = Card(results_frame)
                rc.pack(fill="x", pady=6, ipady=4)

                inner = ctk.CTkFrame(rc, fg_color="transparent")
                inner.pack(fill="x", padx=20, pady=14)

                # Left info
                info = ctk.CTkFrame(inner, fg_color="transparent")
                info.pack(side="left", fill="both", expand=True)

                ctk.CTkLabel(info, text=f"🌐  {web.capitalize()}",
                             font=(FONT_FAMILY, 16, "bold"),
                             text_color=PALETTE["text"]).pack(anchor="w")
                ctk.CTkLabel(info, text=f"👤  {data['username']}",
                             font=(FONT_FAMILY, 12),
                             text_color=PALETTE["text_dim"]).pack(anchor="w", pady=2)
                ctk.CTkLabel(info, text=f"🔗  {data['url']}",
                             font=(FONT_FAMILY, 11),
                             text_color=PALETTE["text_muted"]).pack(anchor="w")

                # Right actions
                right = ctk.CTkFrame(inner, fg_color="transparent")
                right.pack(side="right", padx=(20, 0))

                s_color = {"Strong": PALETTE["success"], "Medium": PALETTE["warning"],
                           "Weak": PALETTE["danger"]}[s]
                ctk.CTkLabel(right, text=s, font=(FONT_FAMILY, 12, "bold"),
                             text_color=s_color).pack(pady=(0, 8))

                GhostButton(right, text="🔑 Copy Password", width=150,
                            command=lambda p=pw: copy_to_clipboard(p, self)).pack(pady=2)
                GhostButton(right, text="👤 Copy Username", width=150,
                            command=lambda u=data["username"]: copy_to_clipboard(u, self)).pack(pady=2)

        e_search.bind("<Return>", lambda e: _do_search())

    # ─────────────────────────────────────────────────────────────────────
    # PAGE: UPDATE
    # ─────────────────────────────────────────────────────────────────────

    def _page_update(self):
        self._reload_vault()
        frame = self._scrollable()
        SectionTitle(frame, text="Update Password").pack(anchor="w", pady=(0, 20))

        if not self._vault:
            ctk.CTkLabel(frame, text="No passwords stored yet.",
                         font=(FONT_FAMILY, 15),
                         text_color=PALETTE["text_muted"]).pack(pady=60)
            return

        card = Card(frame)
        card.pack(fill="x", ipady=10)

        FieldLabel(card, text="SELECT WEBSITE").pack(anchor="w", padx=24, pady=(20, 6))
        sites = list(self._vault.keys())
        combo = ctk.CTkComboBox(card, values=sites, width=400,
                                 fg_color=PALETTE["surface"],
                                 border_color=PALETTE["border"],
                                 button_color=PALETTE["accent"],
                                 button_hover_color=PALETTE["accent_dim"],
                                 dropdown_fg_color=PALETTE["surface2"],
                                 font=(FONT_FAMILY, 13),
                                 text_color=PALETTE["text"])
        combo.pack(padx=24, anchor="w")

        # Fields
        FieldLabel(card, text="NEW USERNAME (leave blank to keep)").pack(anchor="w", padx=24, pady=(16, 4))
        e_user = FormEntry(card, width=400)
        e_user.pack(padx=24, anchor="w")

        FieldLabel(card, text="NEW PASSWORD (leave blank to keep)").pack(anchor="w", padx=24, pady=(16, 4))
        pw_row = ctk.CTkFrame(card, fg_color="transparent")
        pw_row.pack(padx=24, anchor="w")
        e_pass = FormEntry(pw_row, show="●", width=350)
        e_pass.pack(side="left")

        show_var = ctk.BooleanVar()
        def _tog():
            show_var.set(not show_var.get())
            e_pass.configure(show="" if show_var.get() else "●")
        ctk.CTkButton(pw_row, text="👁", width=44, height=44,
                      fg_color=PALETTE["surface"], hover_color=PALETTE["border"],
                      corner_radius=10, command=_tog).pack(side="left", padx=6)

        strength_lbl = ctk.CTkLabel(card, text="",
                                     font=(FONT_FAMILY, 12),
                                     text_color=PALETTE["text_muted"])
        strength_lbl.pack(anchor="w", padx=24, pady=4)

        def _upd_str(*_):
            pw = e_pass.get()
            if not pw:
                strength_lbl.configure(text=""); return
            s = check_password_strength(pw)
            c = {"Strong": PALETTE["success"], "Medium": PALETTE["warning"],
                 "Weak": PALETTE["danger"]}[s]
            strength_lbl.configure(text=f"Strength: {s}", text_color=c)
        e_pass.bind("<KeyRelease>", _upd_str)

        def _save():
            site     = combo.get().strip().lower()
            new_user = e_user.get().strip()
            new_pw   = e_pass.get()
            if site not in self._vault:
                self.show_toast("⚠️  Website not found.", kind="error"); return
            if new_pw and check_password_strength(new_pw) == "Weak":
                self.show_toast("⚠️  Password too weak.", kind="error"); return
            if new_user:
                self._vault[site]["username"] = new_user
            if new_pw:
                self._vault[site]["password"] = encrypt_password(new_pw)
            save_data(self._vault)
            self.show_toast("✅  Updated successfully!")
            e_user.delete(0, "end")
            e_pass.delete(0, "end")
            strength_lbl.configure(text="")

        PrimaryButton(card, text="💾  Save Changes", width=200,
                      command=_save).pack(padx=24, pady=20, anchor="w")

    # ─────────────────────────────────────────────────────────────────────
    # PAGE: DELETE
    # ─────────────────────────────────────────────────────────────────────

    def _page_delete(self):
        self._reload_vault()
        frame = self._scrollable()
        SectionTitle(frame, text="Delete Password").pack(anchor="w", pady=(0, 20))

        if not self._vault:
            ctk.CTkLabel(frame, text="No passwords stored yet.",
                         font=(FONT_FAMILY, 15),
                         text_color=PALETTE["text_muted"]).pack(pady=60)
            return

        card = Card(frame)
        card.pack(fill="x", ipady=10)

        FieldLabel(card, text="SELECT WEBSITE TO DELETE").pack(anchor="w", padx=24, pady=(20, 6))
        sites = list(self._vault.keys())
        combo = ctk.CTkComboBox(card, values=sites, width=400,
                                 fg_color=PALETTE["surface"],
                                 border_color=PALETTE["border"],
                                 button_color=PALETTE["danger"],
                                 button_hover_color="#C0392B",
                                 dropdown_fg_color=PALETTE["surface2"],
                                 font=(FONT_FAMILY, 13),
                                 text_color=PALETTE["text"])
        combo.pack(padx=24, anchor="w")

        # Preview card
        preview = Card(card)
        preview.pack(padx=24, pady=16, fill="x", ipadx=10, ipady=6)
        preview_lbl = ctk.CTkLabel(preview, text="Select a website above to preview.",
                                    font=(FONT_FAMILY, 13),
                                    text_color=PALETTE["text_muted"])
        preview_lbl.pack(padx=16, pady=14)

        def _update_preview(*_):
            for w in preview.winfo_children():
                w.destroy()
            site = combo.get().strip().lower()
            if site not in self._vault:
                ctk.CTkLabel(preview, text="Website not found.",
                             font=(FONT_FAMILY, 13),
                             text_color=PALETTE["text_muted"]).pack(padx=16, pady=14)
                return
            data = self._vault[site]
            ctk.CTkLabel(preview, text=f"🌐  {site.capitalize()}",
                         font=(FONT_FAMILY, 15, "bold"),
                         text_color=PALETTE["danger"]).pack(anchor="w", padx=16, pady=(14, 4))
            ctk.CTkLabel(preview, text=f"👤  {data['username']}",
                         font=(FONT_FAMILY, 12), text_color=PALETTE["text_dim"]).pack(anchor="w", padx=16)
            ctk.CTkLabel(preview, text=f"🔗  {data['url']}",
                         font=(FONT_FAMILY, 11), text_color=PALETTE["text_muted"]).pack(anchor="w", padx=16, pady=(2, 14))

        combo.bind("<ComboboxSelected>", _update_preview)
        combo.bind("<KeyRelease>",       _update_preview)

        def _delete():
            site = combo.get().strip().lower()
            if site not in self._vault:
                self.show_toast("⚠️  Website not found.", kind="error"); return

            def _confirm():
                del self._vault[site]
                save_data(self._vault)
                self.show_toast(f"🗑  '{site}' deleted.")
                self._show_page("delete")

            ConfirmDialog(self, "Confirm Delete",
                          f"Permanently delete '{site}' and its credentials?",
                          on_confirm=_confirm)

        DangerButton(card, text="🗑  Delete Entry", width=200,
                     command=_delete).pack(padx=24, pady=(0, 20), anchor="w")

    # ─────────────────────────────────────────────────────────────────────
    # PAGE: PASSWORD GENERATOR
    # ─────────────────────────────────────────────────────────────────────

    def _page_generator(self):
        frame = self._scrollable()
        SectionTitle(frame, text="Password Generator").pack(anchor="w", pady=(0, 20))

        card = Card(frame)
        card.pack(fill="x", ipady=10)

        # Length slider
        FieldLabel(card, text="LENGTH").pack(anchor="w", padx=24, pady=(20, 6))
        len_row = ctk.CTkFrame(card, fg_color="transparent")
        len_row.pack(padx=24, fill="x")
        len_var = ctk.IntVar(value=16)
        len_lbl = ctk.CTkLabel(len_row, text="16",
                               font=(FONT_MONO, 15, "bold"),
                               text_color=PALETTE["accent"],
                               width=36)
        len_lbl.pack(side="right")

        def _upd_len(v):
            len_var.set(int(float(v)))
            len_lbl.configure(text=str(int(float(v))))

        ctk.CTkSlider(len_row, from_=8, to=32, number_of_steps=24,
                      variable=len_var,
                      command=_upd_len,
                      progress_color=PALETTE["accent"],
                      button_color=PALETTE["accent"],
                      button_hover_color=PALETTE["accent_dim"]).pack(side="left", fill="x", expand=True)

        # Checkboxes
        FieldLabel(card, text="CHARACTER SETS").pack(anchor="w", padx=24, pady=(20, 10))
        chk_frame = ctk.CTkFrame(card, fg_color="transparent")
        chk_frame.pack(padx=24, anchor="w")

        checks = {}
        for label, key, default in [("Uppercase  A–Z", "upper", True),
                                      ("Lowercase  a–z", "lower", True),
                                      ("Numbers  0–9",   "digits", True),
                                      ("Symbols  !@#$",  "symbols", True)]:
            var = ctk.BooleanVar(value=default)
            checks[key] = var
            ctk.CTkCheckBox(chk_frame, text=label, variable=var,
                             font=(FONT_FAMILY, 13),
                             text_color=PALETTE["text"],
                             fg_color=PALETTE["accent"],
                             hover_color=PALETTE["accent_dim"],
                             checkmark_color="#fff").pack(anchor="w", pady=5)

        # Generated password display
        FieldLabel(card, text="GENERATED PASSWORD").pack(anchor="w", padx=24, pady=(20, 6))
        gen_var = ctk.StringVar(value="")
        gen_entry = ctk.CTkEntry(card, textvariable=gen_var,
                                  font=(FONT_MONO, 16),
                                  fg_color=PALETTE["bg"],
                                  border_color=PALETTE["accent"],
                                  border_width=2,
                                  corner_radius=10,
                                  text_color=PALETTE["accent"],
                                  height=52,
                                  state="readonly")
        gen_entry.pack(padx=24, fill="x")

        # Strength indicator
        str_lbl = ctk.CTkLabel(card, text="",
                               font=(FONT_FAMILY, 12),
                               text_color=PALETTE["text_muted"])
        str_lbl.pack(anchor="w", padx=24, pady=(6, 0))

        def _generate():
            length = len_var.get()
            pw = generate_password(length=length,
                                   use_upper=checks["upper"].get(),
                                   use_lower=checks["lower"].get(),
                                   use_digits=checks["digits"].get(),
                                   use_symbols=checks["symbols"].get())
            gen_var.set(pw)
            s = check_password_strength(pw)
            c = {"Strong": PALETTE["success"], "Medium": PALETTE["warning"],
                 "Weak": PALETTE["danger"]}[s]
            str_lbl.configure(text=f"Strength: {s}", text_color=c)

        def _copy():
            pw = gen_var.get()
            if pw:
                copy_to_clipboard(pw, self)
            else:
                self.show_toast("⚠️  Generate a password first.", kind="error")

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(padx=24, pady=20, anchor="w")
        PrimaryButton(btn_row, text="🎲  Generate",     width=160, command=_generate).pack(side="left", padx=(0, 12))
        GhostButton(btn_row,   text="📋  Copy",         width=120, command=_copy).pack(side="left")

        _generate()  # auto-generate on page load

    # ─────────────────────────────────────────────────────────────────────
    # LOGOUT / CLOSE
    # ─────────────────────────────────────────────────────────────────────

    def _logout(self):
        self.destroy()
        if self._on_logout_cb:
            self._on_logout_cb()

    def _on_close(self):
        self.destroy()
        if self._on_logout_cb:
            self._on_logout_cb()


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = LoginWindow()
    app.mainloop()