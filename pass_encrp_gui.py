import os
import json
import secrets
import string
import hashlib
from urllib.parse import urlparse

import customtkinter as ctk
import customtkinter as ctk
from tkinter import messagebox

try:
    from customtkinter import CTkMessageBox
except ImportError:
    CTkMessageBox = None
    
from tkinter import messagebox
from cryptography.fernet import Fernet
import pyperclip

# --- Configuration & Styling ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

FILE_NAME = "vault.json"
KEY_FILE = "key.key"
MASTER_FILE = "master.key"


# --- Core Backend Logic ---

def load_key():
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as f:
            f.write(key)
        return key
    with open(KEY_FILE, "rb") as f:
        return f.read()

KEY = load_key()
CIPHER = Fernet(KEY)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_data():
    try:
        with open(FILE_NAME, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_data(vault):
    with open(FILE_NAME, "w") as f:
        json.dump(vault, f, indent=4)

def valid_url(url):
    result = urlparse(url)
    return all([result.scheme, result.netloc])

def check_password_strength(password):
    length = len(password)
    has_lower = any(c.islower() for c in password)
    has_upper = any(c.isupper() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_symbol = any(c in "!@#$%^&*" for c in password)
    score = sum([has_lower, has_upper, has_digit, has_symbol])

    if length >= 12 and score == 4:
        return "Strong", "#2ecc71"  # Green
    elif length >= 8 and score >= 3:
        return "Medium", "#f39c12"  # Orange
    else:
        return "Weak", "#e74c3c"    # Red

def generate_password(length=12):
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    while True:
        password = ''.join(secrets.choice(chars) for _ in range(length))
        if (any(c.islower() for c in password)
                and any(c.isupper() for c in password)
                and sum(c.isdigit() for c in password) >= 3):
            return password


# --- Main Application ---

class PasswordManagerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("KeyVault - Password Manager")
        self.geometry("850x550")
        self.resizable(False, False)

        self.vault = load_data()

        # Start with Auth Screen
        self.show_auth_screen()

    # ------------------------------------------------------------------
    #  AUTHENTICATION / MASTER PASSWORD SCREENS
    # ------------------------------------------------------------------

    def clear_screen(self):
        for widget in self.winfo_children():
            widget.destroy()

    def show_auth_screen(self):
        self.clear_screen()

        frame = ctk.CTkFrame(self, corner_radius=15)
        frame.pack(expand=True, fill="both", padx=100, pady=80)

        title = ctk.CTkLabel(frame, text="🔒 KeyVault", font=ctk.CTkFont(size=28, weight="bold"))
        title.pack(pady=(40, 10))

        if not os.path.exists(MASTER_FILE):
            sub_title = ctk.CTkLabel(frame, text="Set up your Master Password", font=ctk.CTkFont(size=14))
            sub_title.pack(pady=(0, 20))

            pass_entry = ctk.CTkEntry(frame, placeholder_text="Create Master Password", show="•", width=280)
            pass_entry.pack(pady=8)

            confirm_entry = ctk.CTkEntry(frame, placeholder_text="Confirm Master Password", show="•", width=280)
            confirm_entry.pack(pady=8)

            def set_master():
                p1, p2 = pass_entry.get(), confirm_entry.get()
                if not p1:
                    messagebox.showerror("Error", "Password cannot be empty!")
                    return
                if p1 != p2:
                    messagebox.showerror("Error", "Passwords do not match!")
                    return

                with open(MASTER_FILE, "w") as f:
                    f.write(hash_password(p1))
                messagebox.showinfo("Success", "Master password set successfully!")
                self.show_dashboard()

            ctk.CTkButton(frame, text="Create Vault", command=set_master, width=280, height=35).pack(pady=20)

        else:
            sub_title = ctk.CTkLabel(frame, text="Enter Master Password to Unlock", font=ctk.CTkFont(size=14))
            sub_title.pack(pady=(0, 20))

            pass_entry = ctk.CTkEntry(frame, placeholder_text="Master Password", show="•", width=280)
            pass_entry.pack(pady=10)

            def unlock():
                with open(MASTER_FILE, "r") as f:
                    stored_hash = f.read()

                if hash_password(pass_entry.get()) == stored_hash:
                    self.show_dashboard()
                else:
                    messagebox.showerror("Access Denied", "Incorrect Master Password!")

            pass_entry.bind("<Return>", lambda e: unlock())
            ctk.CTkButton(frame, text="Unlock Vault", command=unlock, width=280, height=35).pack(pady=15)

    # ------------------------------------------------------------------
    #  MAIN DASHBOARD
    # ------------------------------------------------------------------

    def show_dashboard(self):
        self.clear_screen()

        # Main Layout: Left Sidebar + Right Display Panel
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")

        self.main_panel = ctk.CTkFrame(self, corner_radius=10)
        self.main_panel.pack(side="right", fill="both", expand=True, padx=15, pady=15)

        # Sidebar Title
        ctk.CTkLabel(self.sidebar, text="🔒 KeyVault", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=25, padx=20)

        # Nav Buttons
        ctk.CTkButton(self.sidebar, text="➕ Add Entry", command=self.open_add_dialog, width=180, height=35).pack(pady=10)
        ctk.CTkButton(self.sidebar, text="🔑 Generate Pass", command=self.open_generator_dialog, width=180, height=35, fg_color="gray30", hover_color="gray25").pack(pady=5)
        ctk.CTkButton(self.sidebar, text="🚪 Lock Vault", command=self.show_auth_screen, width=180, height=35, fg_color="#c0392b", hover_color="#a93226").pack(side="bottom", pady=25)

        # Search Bar
        search_frame = ctk.CTkFrame(self.main_panel, fg_color="transparent")
        search_frame.pack(fill="x", padx=10, pady=(10, 5))

        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="🔍 Search entries by name...")
        self.search_entry.pack(fill="x")
        self.search_entry.bind("<KeyRelease>", self.filter_vault)

        # Scrollable Frame for Passwords
        self.scroll_frame = ctk.CTkScrollableFrame(self.main_panel, label_text="Stored Credentials")
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.render_vault_list()

    def render_vault_list(self, filter_query=""):
        # Clear existing items
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        filtered_keys = [k for k in self.vault.keys() if filter_query.lower() in k.lower()]

        if not filtered_keys:
            ctk.CTkLabel(self.scroll_frame, text="No entries found.", text_color="gray").pack(pady=20)
            return

        for web in filtered_keys:
            item = self.vault[web]

            # Card Frame
            card = ctk.CTkFrame(self.scroll_frame, corner_radius=8)
            card.pack(fill="x", pady=5, padx=5)

            # Details Text
            info_frame = ctk.CTkFrame(card, fg_color="transparent")
            info_frame.pack(side="left", padx=10, pady=8, fill="x", expand=True)

            ctk.CTkLabel(info_frame, text=web.capitalize(), font=ctk.CTkFont(size=15, weight="bold"), anchor="w").pack(fill="x")
            ctk.CTkLabel(info_frame, text=f"User: {item['username']}", font=ctk.CTkFont(size=12), text_color="gray70", anchor="w").pack(fill="x")

            # Actions Frame
            action_frame = ctk.CTkFrame(card, fg_color="transparent")
            action_frame.pack(side="right", padx=10)

            # Copy Password Button
            def make_copy_cmd(pw_enc):
                return lambda: self.copy_password(pw_enc)

            # Edit Button
            def make_edit_cmd(w):
                return lambda: self.open_edit_dialog(w)

            # Delete Button
            def make_del_cmd(w):
                return lambda: self.delete_entry(w)

            ctk.CTkButton(action_frame, text="Copy", width=60, height=28, command=make_copy_cmd(item["password"])).pack(side="left", padx=2)
            ctk.CTkButton(action_frame, text="Edit", width=60, height=28, fg_color="gray35", hover_color="gray25", command=make_edit_cmd(web)).pack(side="left", padx=2)
            ctk.CTkButton(action_frame, text="🗑", width=35, height=28, fg_color="#e74c3c", hover_color="#c0392b", command=make_del_cmd(web)).pack(side="left", padx=2)

    def filter_vault(self, event=None):
        query = self.search_entry.get()
        self.render_vault_list(filter_query=query)

    def copy_password(self, encrypted_password):
        password = CIPHER.decrypt(encrypted_password.encode()).decode()
        pyperclip.copy(password)
        messagebox.showinfo("Clipboard", "Password copied to clipboard!")

    def delete_entry(self, website):
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{website}'?"):
            del self.vault[website]
            save_data(self.vault)
            self.render_vault_list(self.search_entry.get())

    # ------------------------------------------------------------------
    #  MODAL DIALOGS (Add, Edit, Generate)
    # ------------------------------------------------------------------

    def open_add_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Add New Credential")
        dialog.geometry("400x480")
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Add Website Credential", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=15)

        web_entry = ctk.CTkEntry(dialog, placeholder_text="Website Name (e.g. github)", width=300)
        web_entry.pack(pady=8)

        url_entry = ctk.CTkEntry(dialog, placeholder_text="Website URL (https://...)", width=300)
        url_entry.pack(pady=8)

        user_entry = ctk.CTkEntry(dialog, placeholder_text="Username / Email", width=300)
        user_entry.pack(pady=8)

        pass_entry = ctk.CTkEntry(dialog, placeholder_text="Password", show="•", width=300)
        pass_entry.pack(pady=8)

        strength_label = ctk.CTkLabel(dialog, text="Strength: -", font=ctk.CTkFont(size=12))
        strength_label.pack(pady=2)

        def update_strength(event=None):
            p = pass_entry.get()
            if p:
                str_text, color = check_password_strength(p)
                strength_label.configure(text=f"Strength: {str_text}", text_color=color)
            else:
                strength_label.configure(text="Strength: -", text_color="gray")

        pass_entry.bind("<KeyRelease>", update_strength)

        def auto_gen():
            pw = generate_password()
            pass_entry.delete(0, "end")
            pass_entry.insert(0, pw)
            update_strength()

        ctk.CTkButton(dialog, text="⚡ Generate Random Password", command=auto_gen, fg_color="gray30", width=300).pack(pady=5)

        def save():
            web = web_entry.get().strip().lower()
            url = url_entry.get().strip()
            username = user_entry.get().strip()
            password = pass_entry.get()

            if not web or not username or not password:
                messagebox.showerror("Error", "All fields are required!", parent=dialog)
                return

            if not valid_url(url):
                messagebox.showerror("Error", "Invalid URL scheme! Include http:// or https://", parent=dialog)
                return

            if web in self.vault:
                messagebox.showerror("Error", "Website entry already exists!", parent=dialog)
                return

            encrypted_password = CIPHER.encrypt(password.encode()).decode()
            self.vault[web] = {
                "username": username,
                "password": encrypted_password,
                "url": url
            }
            save_data(self.vault)
            self.render_vault_list(self.search_entry.get())
            dialog.destroy()

        ctk.CTkButton(dialog, text="Save Entry", command=save, width=300, height=35).pack(pady=20)

    def open_edit_dialog(self, website):
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Edit {website.capitalize()}")
        dialog.geometry("400x380")
        dialog.grab_set()

        item = self.vault[website]
        decrypted_pass = CIPHER.decrypt(item["password"].encode()).decode()

        ctk.CTkLabel(dialog, text=f"Edit {website.capitalize()}", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=15)

        user_entry = ctk.CTkEntry(dialog, placeholder_text="Username", width=300)
        user_entry.insert(0, item["username"])
        user_entry.pack(pady=10)

        pass_entry = ctk.CTkEntry(dialog, placeholder_text="New Password", width=300)
        pass_entry.insert(0, decrypted_pass)
        pass_entry.pack(pady=10)

        def update():
            new_user = user_entry.get().strip()
            new_pass = pass_entry.get()

            if not new_user or not new_pass:
                messagebox.showerror("Error", "Fields cannot be empty!", parent=dialog)
                return

            self.vault[website]["username"] = new_user
            self.vault[website]["password"] = CIPHER.encrypt(new_pass.encode()).decode()

            save_data(self.vault)
            self.render_vault_list(self.search_entry.get())
            dialog.destroy()

        ctk.CTkButton(dialog, text="Update Entry", command=update, width=300, height=35).pack(pady=20)

    def open_generator_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Password Generator")
        dialog.geometry("380x280")
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Standalone Generator", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=15)

        gen_entry = ctk.CTkEntry(dialog, width=280, font=ctk.CTkFont(size=14))
        gen_entry.pack(pady=10)

        strength_lbl = ctk.CTkLabel(dialog, text="")
        strength_lbl.pack(pady=2)

        def refresh():
            pw = generate_password()
            gen_entry.delete(0, "end")
            gen_entry.insert(0, pw)
            str_text, color = check_password_strength(pw)
            strength_lbl.configure(text=f"Strength: {str_text}", text_color=color)

        refresh()

        def copy():
            pyperclip.copy(gen_entry.get())
            messagebox.showinfo("Copied", "Generated password copied!", parent=dialog)

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=15)

        ctk.CTkButton(btn_frame, text="🔄 Regenerate", command=refresh, width=130).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="📋 Copy", command=copy, width=130).pack(side="left", padx=5)


if __name__ == "__main__":
    app = PasswordManagerApp()
    app.mainloop()