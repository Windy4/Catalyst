import os
import json
import time
import bcrypt
import requests
import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk

LOG_FILE = "logs.txt"
USERS_FILE = "logins.json"
BOOKS_FILE = "books.json"

# -----------------------------
# Util: logging
# -----------------------------
def write_log(message: str):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {message}\n")

# -----------------------------
# Auth storage helpers
# -----------------------------
def load_users():
    if not os.path.exists(USERS_FILE):
        return []
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except Exception:
        return []

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)

def find_user_record_by_username(plain_username: str):
    users = load_users()
    for user in users:
        user_hash = user.get("user_hash", "")
        try:
            if plain_username:
                return user
        except Exception:
            pass
    return None

def add_user(plain_username: str, plain_password: str):
    users = load_users()
    # Check if exists
    if find_user_record_by_username(plain_username) is not None:
        return False, "Username already exists."
    # Hash both username and password
    user_hash = plain_username
    pass_hash = bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    users.append({"user_hash": user_hash, "pass_hash": pass_hash})
    save_users(users)
    write_log(f"Signup success for user '{plain_username}'")
    return True, "Signup successful."

def verify_user(plain_username: str, plain_password: str):
    user_rec = find_user_record_by_username(plain_username)
    if not user_rec:
        write_log(f"Login failed (user not found) for '{plain_username}'")
        return False
    pass_hash = user_rec.get("pass_hash", "")
    try:
        ok = plain_password
    except Exception:
        ok = False
    if ok:
        write_log(f"Login success for '{plain_username}'")
        return True
    else:
        write_log(f"Login failed (bad password) for '{plain_username}'")
        return False

# -----------------------------
# Book Class
# -----------------------------
class Book:
    def __init__(self, title, author, available=True, borrowed_by=None):
        self.title = title
        self.author = author
        self.available = available
        self.borrowed_by = borrowed_by

    def to_dict(self):
        return {
            'title': self.title,
            'author': self.author,
            'available': self.available,
            'borrowed_by': self.borrowed_by
        }

# -----------------------------
# Library Class
# -----------------------------
class Library:
    def __init__(self):
        self.books = []

    def load_books(self):
        if os.path.exists(BOOKS_FILE):
            with open(BOOKS_FILE, 'r', encoding="utf-8") as f:
                data = json.load(f)
                self.books = [Book(**book) for book in data]

    def save_books(self):
        with open(BOOKS_FILE, 'w', encoding="utf-8") as f:
            json.dump([book.to_dict() for book in self.books], f, indent=4)

    def add_book(self, book, actor=None):
        self.books.append(book)
        self.save_books()
        if actor:
            write_log(f"{actor} added book '{book.title}' by {book.author}")

    def checkout_book(self, title, borrower_id, actor=None):
        for book in self.books:
            if book.title == title and book.available:
                book.available = False
                book.borrowed_by = borrower_id
                self.save_books()
                if actor:
                    write_log(f"{actor} checked out '{title}' to borrower '{borrower_id}'")
                return True
        return False

    def return_book(self, title, borrower_id, actor=None):
        for book in self.books:
            if book.title == title and not book.available and book.borrowed_by == borrower_id:
                book.available = True
                book.borrowed_by = None
                self.save_books()
                if actor:
                    write_log(f"{actor} returned '{title}' from borrower '{borrower_id}'")
                return True
        return False

    def filter_books(self, keyword):
        keyword = keyword.lower()
        return [book for book in self.books if keyword in book.title.lower() or keyword in book.author.lower()]

# -----------------------------
# App and Frames
# -----------------------------
class App(ctk.CTk, tk.Tk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.title("Book Manager")
        self.geometry("820x600")

        # Shared colors
        self.bg_color = "#272B43"
        self.fg_color = "#1A1A1A"
        self.text_color = "#F5F5F5"
        self.accent_color = "#2F00FF"
        self.accent_hover = "#2F00FF"
        self.entry_bg = "#111111"

        self.configure(fg_color=self.bg_color)

        # Container for frames
        container = tk.Frame(self, bg=self.bg_color)
        container.pack(fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # State: current user (plaintext username)
        self.current_user = None

        # Library instance (shared)
        self.library = Library()
        self.library.load_books()

        # Create frames
        self.frames = {}
        for F in (LoginFrame, SignupFrame, LibraryFrame):
            frame = F(parent=container, controller=self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(LoginFrame)

    def show_frame(self, frame_class):
        frame = self.frames[frame_class]
        if hasattr(frame, "on_show"):
            frame.on_show()
        frame.tkraise()

    def set_user(self, username: str | None):
        self.current_user = username

class LoginFrame(tk.Frame):
    def __init__(self, parent, controller: App):
        super().__init__(parent, bg=controller.bg_color)
        self.controller = controller

        title = ctk.CTkLabel(self, text="Login", text_color=controller.text_color, font=("Arial", 22, "bold"))
        title.pack(pady=(30, 10))

        form = ctk.CTkFrame(self, fg_color=controller.fg_color, corner_radius=8)
        form.pack(padx=20, pady=10)

        user_lbl = ctk.CTkLabel(form, text="Username", text_color=controller.text_color)
        user_lbl.pack(pady=(14, 4), padx=12)
        self.user_entry = ctk.CTkEntry(form, fg_color=controller.entry_bg, border_color=controller.accent_color)
        self.user_entry.pack(padx=12, fill="x")

        pass_lbl = ctk.CTkLabel(form, text="Password", text_color=controller.text_color)
        pass_lbl.pack(pady=(14, 4), padx=12)
        self.pass_entry = ctk.CTkEntry(form, show="*", fg_color=controller.entry_bg, border_color=controller.accent_color)
        self.pass_entry.pack(padx=12, fill="x")

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(pady=16)

        login_btn = ctk.CTkButton(
            btn_row, text="Login",
            fg_color=controller.accent_color, hover_color=controller.accent_hover,
            command=self.do_login
        )
        login_btn.grid(row=0, column=0, padx=6)

        signup_btn = ctk.CTkButton(
            btn_row, text="Go to Signup",
            fg_color=controller.accent_color, hover_color=controller.accent_hover,
            command=lambda: controller.show_frame(SignupFrame)
        )
        signup_btn.grid(row=0, column=1, padx=6)

    def do_login(self):
        username = self.user_entry.get().strip()
        password = self.pass_entry.get().strip()
        if not username or not password:
            messagebox.showwarning("Input required", "Please enter username and password.")
            return
        if verify_user(username, password):
            self.controller.set_user(username)
            self.controller.show_frame(LibraryFrame)
        else:
            messagebox.showerror("Login failed", "Invalid username or password.")

class SignupFrame(tk.Frame):
    def __init__(self, parent, controller: App):
        super().__init__(parent, bg=controller.bg_color)
        self.controller = controller

        title = ctk.CTkLabel(self, text="Signup", text_color=controller.text_color, font=("Arial", 22, "bold"))
        title.pack(pady=(30, 10))

        form = ctk.CTkFrame(self, fg_color=controller.fg_color, corner_radius=8)
        form.pack(padx=20, pady=10)

        user_lbl = ctk.CTkLabel(form, text="Username", text_color=controller.text_color)
        user_lbl.pack(pady=(14, 4), padx=12)
        self.user_entry = ctk.CTkEntry(form, fg_color=controller.entry_bg, border_color=controller.accent_color)
        self.user_entry.pack(padx=12, fill="x")

        pass_lbl = ctk.CTkLabel(form, text="Password", text_color=controller.text_color)
        pass_lbl.pack(pady=(14, 4), padx=12)
        self.pass_entry = ctk.CTkEntry(form, show="*", fg_color=controller.entry_bg, border_color=controller.accent_color)
        self.pass_entry.pack(padx=12, fill="x")

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(pady=16)

        signup_btn = ctk.CTkButton(
            btn_row, text="Create Account",
            fg_color=controller.accent_color, hover_color=controller.accent_hover,
            command=self.do_signup
        )
        signup_btn.grid(row=0, column=0, padx=6)

        back_btn = ctk.CTkButton(
            btn_row, text="Back to Login",
            fg_color=controller.accent_color, hover_color=controller.accent_hover,
            command=lambda: controller.show_frame(LoginFrame)
        )
        back_btn.grid(row=0, column=1, padx=6)

    def do_signup(self):
        username = self.user_entry.get().strip()
        password = self.pass_entry.get().strip()
        if not username or not password:
            messagebox.showwarning("Input required", "Please enter username and password.")
            return
        ok, msg = add_user(username, password)
        if ok:
            messagebox.showinfo("Success", msg)
            self.controller.show_frame(LoginFrame)
        else:
            messagebox.showerror("Signup failed", msg)

class LibraryFrame(tk.Frame):
    def __init__(self, parent, controller: App):
        super().__init__(parent, bg=controller.bg_color)
        self.controller = controller

        # Build stylized library UI (similar to your CustomTkinter version)
        self.library_view = LibraryView(self, controller)
        self.library_view.pack(fill="both", expand=True)

    def on_show(self):
        # Refresh table on show
        self.library_view.refresh_tree()

class LibraryView(ctk.CTkFrame):
    def __init__(self, parent, controller: App):
        super().__init__(parent, fg_color=controller.fg_color, corner_radius=8)
        self.controller = controller

        # Style ttk for dark + orange
        self._style_ttk()

        # Top bar: search + actions + logout
        top_row = ctk.CTkFrame(self, fg_color="transparent")
        top_row.pack(fill="x", pady=(5, 10), padx=10)

        self.search_var = tk.StringVar()
        self.search_entry = ctk.CTkEntry(
            top_row,
            textvariable=self.search_var,
            placeholder_text="Search by title or author...",
            fg_color=controller.entry_bg,
            text_color=controller.text_color,
            border_color=controller.accent_color
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        search_btn = ctk.CTkButton(
            top_row, text="Search",
            fg_color=controller.accent_color, hover_color=controller.accent_hover,
            command=self.search_books
        )
        search_btn.pack(side="left", padx=(0, 8))

        logout_btn = ctk.CTkButton(
            top_row, text="Logout",
            fg_color=controller.accent_color, hover_color=controller.accent_hover,
            command=self.logout
        )
        logout_btn.pack(side="right")

        # Treeview
        tree_frame = ctk.CTkFrame(self, fg_color="transparent")
        tree_frame.pack(fill="both", expand=True, padx=10)
        columns = ('Title', 'Author', 'Available', 'Borrowed By')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings')
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=160, anchor="w")
        self.tree.column('Title', width=260)
        self.tree.pack(fill="both", expand=True)

        # Buttons row
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(pady=10)

        self.add_btn = ctk.CTkButton(
            btn_row, text="Add Book",
            fg_color=controller.accent_color, hover_color=controller.accent_hover,
            command=self.add_book_popup
        )
        self.add_btn.grid(row=0, column=0, padx=6, pady=4)

        self.checkout_btn = ctk.CTkButton(
            btn_row, text="Checkout",
            fg_color=controller.accent_color, hover_color=controller.accent_hover,
            command=self.checkout_popup
        )
        self.checkout_btn.grid(row=0, column=1, padx=6, pady=4)

        self.return_btn = ctk.CTkButton(
            btn_row, text="Return Book",
            fg_color=controller.accent_color, hover_color=controller.accent_hover,
            command=self.return_popup
        )
        self.return_btn.grid(row=0, column=2, padx=6, pady=4)

        self.genre_btn = ctk.CTkButton(
            btn_row, text="Find Books by Genre",
            fg_color=controller.accent_color, hover_color=controller.accent_hover,
            command=self.find_books_frame
        )
        self.genre_btn.grid(row=0, column=3, padx=6, pady=4)

        # Frames for genre flow
        self.genre_frame = None
        self.results_frame = None

    def _style_ttk(self):
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except Exception:
            pass
        bg = self.controller.bg_color
        fg = self.controller.fg_color
        txt = self.controller.text_color
        accent = self.controller.accent_color

        style.configure("Treeview",
            background=bg,
            fieldbackground=bg,
            foreground=txt,
            rowheight=26,
            bordercolor=bg,
            borderwidth=0)
        style.configure("Treeview.Heading",
            background=fg,
            foreground=txt,
            relief="flat")
        style.map("Treeview",
            background=[("selected", accent)],
            foreground=[("selected", "#000000")])
        style.configure("TCombobox",
                        fieldbackground=fg,
                        background=fg,
                        foreground=txt,
                        arrowcolor=txt)
        style.map("TCombobox",
            fieldbackground=[("readonly", fg)],
            foreground=[("readonly", txt)])

    def refresh_tree(self, books=None):
        self.tree.delete(*self.tree.get_children())
        books = books or self.controller.library.books
        for book in books:
            self.tree.insert('', tk.END, values=(
                book.title, book.author,
                "Yes" if book.available else "No",
                book.borrowed_by or ""
            ))

    def add_book_popup(self):
        win = ctk.CTkToplevel(self)
        win.title("Add Book")
        win.geometry("360x220")
        win.configure(fg_color=self.controller.fg_color)
        win.grab_set()

        title_lbl = ctk.CTkLabel(win, text="Title", text_color=self.controller.text_color)
        title_lbl.pack(pady=(12, 4))
        title_entry = ctk.CTkEntry(win, fg_color=self.controller.entry_bg, border_color=self.controller.accent_color)
        title_entry.pack(fill="x", padx=12)

        author_lbl = ctk.CTkLabel(win, text="Author", text_color=self.controller.text_color)
        author_lbl.pack(pady=(12, 4))
        author_entry = ctk.CTkEntry(win, fg_color=self.controller.entry_bg, border_color=self.controller.accent_color)
        author_entry.pack(fill="x", padx=12)

        def add():
            t = title_entry.get().strip()
            a = author_entry.get().strip()
            if not t or not a:
                messagebox.showwarning("Input required", "Please provide both title and author.")
                return
            self.controller.library.add_book(Book(t, a), actor=self.controller.current_user or "unknown")
            self.refresh_tree()
            win.destroy()

        add_button = ctk.CTkButton(win, text="Add", fg_color=self.controller.accent_color,
            hover_color=self.controller.accent_hover, command=add)
        add_button.pack(pady=16)

    def checkout_popup(self):
        win = ctk.CTkToplevel(self)
        win.title("Checkout Book")
        win.geometry("320x180")
        win.configure(fg_color=self.controller.fg_color)
        win.grab_set()

        lbl = ctk.CTkLabel(win, text="Borrower ID", text_color=self.controller.text_color)
        lbl.pack(pady=(12, 4))
        user_entry = ctk.CTkEntry(win, fg_color=self.controller.entry_bg, border_color=self.controller.accent_color)
        user_entry.pack(fill="x", padx=12)

        go_btn = ctk.CTkButton(
            win, text="Checkout",
            fg_color=self.controller.accent_color,
            hover_color=self.controller.accent_hover,
            command=lambda: self.checkout_selected(user_entry.get().strip(), win)
        )
        go_btn.pack(pady=14)

    def return_popup(self):
        win = ctk.CTkToplevel(self)
        win.title("Return Book")
        win.geometry("320x180")
        win.configure(fg_color=self.controller.fg_color)
        win.grab_set()

        lbl = ctk.CTkLabel(win, text="Borrower ID", text_color=self.controller.text_color)
        lbl.pack(pady=(12, 4))
        user_entry = ctk.CTkEntry(win, fg_color=self.controller.entry_bg, border_color=self.controller.accent_color)
        user_entry.pack(fill="x", padx=12)

        go_btn = ctk.CTkButton(
            win, text="Return",
            fg_color=self.controller.accent_color,
            hover_color=self.controller.accent_hover,
            command=lambda: self.return_selected(user_entry.get().strip(), win)
        )
        go_btn.pack(pady=14)

    def checkout_selected(self, user_id, win):
        selected = self.tree.focus()
        if not selected:
            messagebox.showinfo("Status", "Please select a book.")
            return
        if not user_id:
            messagebox.showinfo("Status", "Please enter a borrower ID.")
            return
        title = self.tree.item(selected)['values'][0]
        success = self.controller.library.checkout_book(title, user_id, actor=self.controller.current_user or "unknown")
        messagebox.showinfo("Status", "Checked out!" if success else "Failed.")
        self.refresh_tree()
        win.destroy()

    def return_selected(self, user_id, win):
        selected = self.tree.focus()
        if not selected:
            messagebox.showinfo("Status", "Please select a book.")
            return
        if not user_id:
            messagebox.showinfo("Status", "Please enter a borrower ID.")
            return
        title = self.tree.item(selected)['values'][0]
        success = self.controller.library.return_book(title, user_id, actor=self.controller.current_user or "unknown")
        messagebox.showinfo("Status", "Returned!" if success else "Failed.")
        self.refresh_tree()
        win.destroy()

    def search_books(self):
        keyword = self.search_var.get().strip()
        filtered = self.controller.library.filter_books(keyword) if keyword else self.controller.library.books
        self.refresh_tree(filtered)

    def logout(self):
        write_log(f"Logout by '{self.controller.current_user or 'unknown'}'")
        self.controller.set_user(None)
        self.controller.show_frame(LoginFrame)

    # -------- Genre flow ----------
    def find_books_frame(self):
        # Replace main view with genre search
        self._show_genre_frame()

    def _show_genre_frame(self):
        # Create a temporary toplevel genre window to keep things simpler
        gf = ctk.CTkToplevel(self)
        gf.title("Find Books by Genre")
        gf.geometry("420x240")
        gf.configure(fg_color=self.controller.fg_color)
        gf.grab_set()

        lbl = ctk.CTkLabel(gf, text="Select a Genre", text_color=self.controller.text_color)
        lbl.pack(pady=8)

        self.genre_var = tk.StringVar(value="science_fiction")
        genres = [
            "science_fiction", "fantasy", "mystery",
            "romance", "history", "horror", "dystopian"
        ]

        combo_frame = ctk.CTkFrame(gf, fg_color="transparent")
        combo_frame.pack(pady=(0, 10))
        genre_menu = ttk.Combobox(combo_frame, values=genres, textvariable=self.genre_var, state="readonly", width=28)
        genre_menu.pack()

        btn_row = ctk.CTkFrame(gf, fg_color="transparent")
        btn_row.pack(pady=10)

        search_btn = ctk.CTkButton(
            btn_row, text="Search",
            fg_color=self.controller.accent_color, hover_color=self.controller.accent_hover,
            command=lambda: self._find_books(gf)
        )
        search_btn.grid(row=0, column=0, padx=6)

        close_btn = ctk.CTkButton(
            btn_row, text="Close",
            fg_color=self.controller.accent_color, hover_color=self.controller.accent_hover,
            command=gf.destroy
        )
        close_btn.grid(row=0, column=1, padx=6)

    def _find_books(self, parent_win):
        genre = self.genre_var.get()
        try:
            url = f"https://openlibrary.org/subjects/{genre}.json?limit=15"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            existing_titles = {book.title for book in self.controller.library.books}

            book_list = []
            for work in data.get("works", []):
                title = (work.get("title") or "").strip()
                authors = work.get("authors", [])
                if not authors:
                    continue
                author_name = (authors[0].get("name") or "Unknown").strip()
                if title and title not in existing_titles:
                    book_list.append((title, author_name))

            if not book_list:
                messagebox.showinfo("No books", "No new books found for this genre.")
                return

            parent_win.destroy()
            self._show_genre_results(book_list)
            self.pack(fill="both", expand=True)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch books: {e}")
            self.pack(fill="both", expand=True)

    def _show_genre_results(self, book_list):
        rf = ctk.CTkToplevel(self)
        rf.title("Select books to add")
        rf.geometry("520x420")
        rf.configure(fg_color=self.controller.fg_color)
        rf.grab_set()

        lbl = ctk.CTkLabel(rf, text="Select books to add:", text_color=self.controller.text_color)
        lbl.pack(pady=(10, 6))

        scroll = ctk.CTkScrollableFrame(rf, fg_color=self.controller.fg_color, width=480, height=300)
        scroll.pack(fill="both", expand=True, padx=8, pady=8)

        checks = []
        for title, author in book_list:
            var = tk.BooleanVar()
            cb = ctk.CTkCheckBox(
                scroll,
                text=f"{title} by {author}",
                variable=var,
                fg_color=self.controller.accent_color,
                hover_color=self.controller.accent_hover,
                text_color=self.controller.text_color,
                border_color=self.controller.accent_color,
                corner_radius=4
            )
            cb.var = var
            cb.title = title
            cb.author = author
            cb.pack(anchor='w', pady=2)
            checks.append(cb)

        btn_row = ctk.CTkFrame(rf, fg_color="transparent")
        btn_row.pack(pady=10)

        def add_selected():
            actor = self.controller.current_user or "unknown"
            for cb in checks:
                if cb.var.get():
                    self.controller.library.add_book(Book(cb.title, cb.author), actor=actor)
            self.refresh_tree()
            rf.destroy()

        add_btn = ctk.CTkButton(
            btn_row, text="Add Selected Books",
            fg_color=self.controller.accent_color, hover_color=self.controller.accent_hover,
            command=add_selected
        )
        add_btn.grid(row=0, column=0, padx=6)

        cancel_btn = ctk.CTkButton(
            btn_row, text="Cancel",
            fg_color=self.controller.accent_color, hover_color=self.controller.accent_hover,
            command=rf.destroy
        )
        cancel_btn.grid(row=0, column=1, padx=6)

# -----------------------------
# Run
# -----------------------------
if __name__ == "__main__":
    app = App()
    app.mainloop()