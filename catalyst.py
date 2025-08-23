import os
import json
import requests
import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk

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


# Library Class
class Library:
    def __init__(self):
        self.books = []

    def load_books(self):
        if os.path.exists('books.json'):
            with open('books.json', 'r') as f:
                data = json.load(f)
                self.books = [Book(**book) for book in data]

    def save_books(self):
        with open('books.json', 'w') as f:
            json.dump([book.to_dict() for book in self.books], f, indent=4)

    def add_book(self, book):
        self.books.append(book)
        self.save_books()

    def checkout_book(self, title, borrower_id):
        for book in self.books:
            if book.title == title and book.available:
                book.available = False
                book.borrowed_by = borrower_id
                self.save_books()
                return True
        return False

    def return_book(self, title, borrower_id):
        for book in self.books:
            if book.title == title and not book.available and book.borrowed_by == borrower_id:
                book.available = True
                book.borrowed_by = None
                self.save_books()
                return True
        return False

    def filter_books(self, keyword):
        keyword = keyword.lower()
        return [book for book in self.books if keyword in book.title.lower() or keyword in book.author.lower()]

#App Class
class LibraryApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Theme and appearance
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")  # base, we'll override with orange accents

        self.title("Library System")
        self.geometry("700x550")

        # Colors
        self.bg_color = "#0F0F0F"          # near black background
        self.fg_color = "#1A1A1A"          # dark frame color
        self.text_color = "#F5F5F5"        # light text
        self.accent_color = "#FF7A00"      # orange
        self.accent_hover = "#FF8F26"      # lighter orange for hover
        self.entry_bg = "#111111"

        self.configure(fg_color=self.bg_color)

        # Style ttk.Treeview and ttk Combobox for dark + orange
        self._style_ttk()

        self.library = Library()
        self.library.load_books()

        self.main_frame = ctk.CTkFrame(self, fg_color=self.fg_color, corner_radius=8)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.build_main_ui()

    def _style_ttk(self):
        style = ttk.Style()
        # Use 'clam' for better dark mode support
        style.theme_use('clam')

        # General colors
        style.configure("Treeview",
            background=self.bg_color,
            fieldbackground=self.bg_color,
            foreground=self.text_color,
            rowheight=26,
            bordercolor=self.bg_color,
            borderwidth=0)
        style.configure("Treeview.Heading",
            background=self.fg_color,
            foreground=self.text_color,
            relief="flat")
        style.map("Treeview",
            background=[("selected", self.accent_color)],
            foreground=[("selected", "#000000")])

        # Combobox styling
        style.configure("TCombobox",
                        fieldbackground=self.fg_color,
                        background=self.fg_color,
                        foreground=self.text_color,
                        arrowcolor=self.text_color)
        style.map("TCombobox",
            fieldbackground=[("readonly", self.fg_color)],
            foreground=[("readonly", self.text_color)])

    def build_main_ui(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        # Search Row
        top_row = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        top_row.pack(fill="x", pady=(5, 10))

        self.search_var = tk.StringVar()
        self.search_entry = ctk.CTkEntry(
            top_row,
            textvariable=self.search_var,
            placeholder_text="Search by title or author...",
            fg_color=self.entry_bg,
            text_color=self.text_color,
            border_color=self.accent_color
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        search_btn = ctk.CTkButton(
            top_row,
            text="Search",
            fg_color=self.accent_color,
            hover_color=self.accent_hover,
            command=self.search_books
        )
        search_btn.pack(side="left")

        # Treeview
        tree_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        tree_frame.pack(fill="both", expand=True)

        columns = ('Title', 'Author', 'Available', 'Borrowed By')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings')

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=140, anchor="w")
        self.tree.column('Title', width=220)

        self.tree.pack(fill="both", expand=True, padx=2, pady=2)

        # Buttons
        btn_row = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_row.pack(pady=10)

        add_btn = ctk.CTkButton(
            btn_row,
            text="Add Book",
            fg_color=self.accent_color,
            hover_color=self.accent_hover,
            command=self.add_book_popup
        )
        add_btn.grid(row=0, column=0, padx=6, pady=4)

        checkout_btn = ctk.CTkButton(
            btn_row,
            text="Checkout",
            fg_color=self.accent_color,
            hover_color=self.accent_hover,
            command=self.checkout_popup
        )
        checkout_btn.grid(row=0, column=1, padx=6, pady=4)

        return_btn = ctk.CTkButton(
            btn_row,
            text="Return Book",
            fg_color=self.accent_color,
            hover_color=self.accent_hover,
            command=self.return_popup
        )
        return_btn.grid(row=0, column=2, padx=6, pady=4)

        genre_btn = ctk.CTkButton(
            btn_row,
            text="Find Books by Genre",
            fg_color=self.accent_color,
            hover_color=self.accent_hover,
            command=self.find_books_frame
        )
        genre_btn.grid(row=0, column=3, padx=6, pady=4)

        self.refresh_tree()

    def refresh_tree(self, books=None):
        self.tree.delete(*self.tree.get_children())
        books = books or self.library.books
        for book in books:
            self.tree.insert('', tk.END, values=(
                book.title, book.author,
                "Yes" if book.available else "No",
                book.borrowed_by or ""
            ))

    # -----------------------------
    # Popups (CustomTkinter)
    # -----------------------------
    def add_book_popup(self):
        win = ctk.CTkToplevel(self)
        win.title("Add Book")
        win.geometry("360x220")
        win.configure(fg_color=self.fg_color)
        win.grab_set()

        title_lbl = ctk.CTkLabel(win, text="Title", text_color=self.text_color)
        title_lbl.pack(pady=(12, 4))
        title_entry = ctk.CTkEntry(win, fg_color=self.entry_bg, border_color=self.accent_color)
        title_entry.pack(fill="x", padx=12)

        author_lbl = ctk.CTkLabel(win, text="Author", text_color=self.text_color)
        author_lbl.pack(pady=(12, 4))
        author_entry = ctk.CTkEntry(win, fg_color=self.entry_bg, border_color=self.accent_color)
        author_entry.pack(fill="x", padx=12)

        def add():
            t = title_entry.get().strip()
            a = author_entry.get().strip()
            if not t or not a:
                messagebox.showwarning("Input required", "Please provide both title and author.")
                return
            self.library.add_book(Book(t, a))
            self.refresh_tree()
            win.destroy()

        add_button = ctk.CTkButton(win, text="Add", fg_color=self.accent_color, hover_color=self.accent_hover, command=add)
        add_button.pack(pady=16)

    def checkout_popup(self):
        win = ctk.CTkToplevel(self)
        win.title("Checkout Book")
        win.geometry("320x180")
        win.configure(fg_color=self.fg_color)
        win.grab_set()

        lbl = ctk.CTkLabel(win, text="Borrower ID", text_color=self.text_color)
        lbl.pack(pady=(12, 4))
        user_entry = ctk.CTkEntry(win, fg_color=self.entry_bg, border_color=self.accent_color)
        user_entry.pack(fill="x", padx=12)

        go_btn = ctk.CTkButton(
            win, text="Checkout",
            fg_color=self.accent_color,
            hover_color=self.accent_hover,
            command=lambda: self.checkout_selected(user_entry.get().strip(), win)
        )
        go_btn.pack(pady=14)

    def return_popup(self):
        win = ctk.CTkToplevel(self)
        win.title("Return Book")
        win.geometry("320x180")
        win.configure(fg_color=self.fg_color)
        win.grab_set()

        lbl = ctk.CTkLabel(win, text="Borrower ID", text_color=self.text_color)
        lbl.pack(pady=(12, 4))
        user_entry = ctk.CTkEntry(win, fg_color=self.entry_bg, border_color=self.accent_color)
        user_entry.pack(fill="x", padx=12)

        go_btn = ctk.CTkButton(
            win, text="Return",
            fg_color=self.accent_color,
            hover_color=self.accent_hover,
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
        success = self.library.checkout_book(title, user_id)
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
        success = self.library.return_book(title, user_id)
        messagebox.showinfo("Status", "Returned!" if success else "Failed.")
        self.refresh_tree()
        win.destroy()

    def search_books(self):
        keyword = self.search_var.get().strip()
        filtered = self.library.filter_books(keyword) if keyword else self.library.books
        self.refresh_tree(filtered)

    # -----------------------------
    # Genre Flow
    # -----------------------------
    def find_books_frame(self):
        self.main_frame.pack_forget()
        self.genre_frame = ctk.CTkFrame(self, fg_color=self.fg_color, corner_radius=8)
        self.genre_frame.pack(fill='both', expand=True, padx=10, pady=10)

        lbl = ctk.CTkLabel(self.genre_frame, text="Select a Genre", text_color=self.text_color)
        lbl.pack(pady=8)

        self.genre_var = tk.StringVar(value="science_fiction")
        genres = [
            "science_fiction", "fantasy", "mystery",
            "romance", "history", "horror", "dystopian"
        ]
        # Using ttk Combobox to keep consistency with Treeview styling
        combo_frame = ctk.CTkFrame(self.genre_frame, fg_color="transparent")
        combo_frame.pack(pady=(0, 10))
        genre_menu = ttk.Combobox(combo_frame, values=genres, textvariable=self.genre_var, state="readonly", width=28)
        genre_menu.pack()

        btn_row = ctk.CTkFrame(self.genre_frame, fg_color="transparent")
        btn_row.pack(pady=10)

        search_btn = ctk.CTkButton(
            btn_row, text="Search",
            fg_color=self.accent_color, hover_color=self.accent_hover,
            command=self.find_books
        )
        search_btn.grid(row=0, column=0, padx=6)

        back_btn = ctk.CTkButton(
            btn_row, text="Back",
            fg_color=self.accent_color, hover_color=self.accent_hover,
            command=self.back_to_main
        )
        back_btn.grid(row=0, column=1, padx=6)

    def find_books(self):
        genre = self.genre_var.get()
        try:
            url = f"https://openlibrary.org/subjects/{genre}.json?limit=15"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            existing_titles = {book.title for book in self.library.books}

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

            self.genre_frame.pack_forget()
            self.show_genre_results(book_list)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch books: {e}")

    def show_genre_results(self, book_list):
        self.results_frame = ctk.CTkFrame(self, fg_color=self.fg_color, corner_radius=8)
        self.results_frame.pack(fill='both', expand=True, padx=10, pady=10)

        lbl = ctk.CTkLabel(self.results_frame, text="Select books to add:", text_color=self.text_color)
        lbl.pack(pady=(10, 6))

        # Scrollable checkbox area
        scroll_frame = ctk.CTkScrollableFrame(self.results_frame, fg_color=self.fg_color)
        scroll_frame.pack(fill="both", expand=True, padx=8, pady=8)

        self._result_checkboxes = []
        for title, author in book_list:
            var = tk.BooleanVar()
            cb = ctk.CTkCheckBox(
                scroll_frame,
                text=f"{title} by {author}",
                variable=var,
                fg_color=self.accent_color,
                hover_color=self.accent_hover,
                text_color=self.text_color,
                border_color=self.accent_color,
                corner_radius=4
            )
            cb.var = var
            cb.title = title
            cb.author = author
            cb.pack(anchor='w', pady=2)
            self._result_checkboxes.append(cb)

        btn_row = ctk.CTkFrame(self.results_frame, fg_color="transparent")
        btn_row.pack(pady=10)

        add_btn = ctk.CTkButton(
            btn_row, text="Add Selected Books",
            fg_color=self.accent_color, hover_color=self.accent_hover,
            command=self._add_selected_books_from_results
        )
        add_btn.grid(row=0, column=0, padx=6)

        back_btn = ctk.CTkButton(
            btn_row, text="Back",
            fg_color=self.accent_color, hover_color=self.accent_hover,
            command=self.return_from_results
        )
        back_btn.grid(row=0, column=1, padx=6)

    def _add_selected_books_from_results(self):
        for cb in getattr(self, "_result_checkboxes", []):
            if cb.var.get():
                self.library.add_book(Book(cb.title, cb.author))
        self.results_frame.destroy()
        self.back_to_main()

    def return_from_results(self):
        self.results_frame.destroy()
        self.find_books_frame()

    def back_to_main(self):
        if hasattr(self, 'genre_frame') and self.genre_frame.winfo_exists():
            self.genre_frame.destroy()
        if hasattr(self, 'results_frame') and self.results_frame.winfo_exists():
            self.results_frame.destroy()
        self.main_frame.pack(fill='both', expand=True)
        self.refresh_tree()

#mainloop
if __name__ == "__main__":
    app = LibraryApp()
    app.mainloop()