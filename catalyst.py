import tkinter as tk
from tkinter import messagebox, ttk
import json
import os
import requests

# Book Class
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

# Tkinter App
class LibraryApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Library System")
        self.geometry("600x500")

        self.library = Library()
        self.library.load_books()

        self.main_frame = tk.Frame(self)
        self.main_frame.pack(fill='both', expand=True)

        self.build_main_ui()

    def build_main_ui(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        self.search_var = tk.StringVar()
        tk.Entry(self.main_frame, textvariable=self.search_var).pack(fill="x")
        tk.Button(self.main_frame, text="Search", command=self.search_books).pack()

        self.tree = ttk.Treeview(self.main_frame, columns=('Title', 'Author', 'Available', 'Borrowed By'), show='headings')
        for col in ('Title', 'Author', 'Available', 'Borrowed By'):
            self.tree.heading(col, text=col)
        self.tree.pack(fill='both', expand=True)

        tk.Button(self.main_frame, text="Add Book", command=self.add_book_popup).pack(pady=5)
        tk.Button(self.main_frame, text="Checkout", command=self.checkout_popup).pack(pady=5)
        tk.Button(self.main_frame, text="Return Book", command=self.return_popup).pack(pady=5)
        tk.Button(self.main_frame, text="Find Books by Genre", command=self.find_books_frame).pack(pady=5)

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

    def add_book_popup(self):
        win = tk.Toplevel(self)
        win.title("Add Book")
        tk.Label(win, text="Title").pack()
        title = tk.Entry(win)
        title.pack()
        tk.Label(win, text="Author").pack()
        author = tk.Entry(win)
        author.pack()

        def add():
            self.library.add_book(Book(title.get(), author.get()))
            self.refresh_tree()
            win.destroy()

        tk.Button(win, text="Add", command=add).pack()

    def checkout_popup(self):
        win = tk.Toplevel(self)
        win.title("Checkout Book")
        tk.Label(win, text="Borrower ID").pack()
        user_id = tk.Entry(win)
        user_id.pack()
        tk.Button(win, text="Checkout", command=lambda: self.checkout_selected(user_id.get(), win)).pack()

    def return_popup(self):
        win = tk.Toplevel(self)
        win.title("Return Book")
        tk.Label(win, text="Borrower ID").pack()
        user_id = tk.Entry(win)
        user_id.pack()
        tk.Button(win, text="Return", command=lambda: self.return_selected(user_id.get(), win)).pack()

    def checkout_selected(self, user_id, win):
        selected = self.tree.focus()
        if not selected:
            return
        title = self.tree.item(selected)['values'][0]
        success = self.library.checkout_book(title, user_id)
        messagebox.showinfo("Status", "Checked out!" if success else "Failed.")
        self.refresh_tree()
        win.destroy()

    def return_selected(self, user_id, win):
        selected = self.tree.focus()
        if not selected:
            return
        title = self.tree.item(selected)['values'][0]
        success = self.library.return_book(title, user_id)
        messagebox.showinfo("Status", "Returned!" if success else "Failed.")
        self.refresh_tree()
        win.destroy()

    def search_books(self):
        keyword = self.search_var.get()
        filtered = self.library.filter_books(keyword)
        self.refresh_tree(filtered)

    def find_books_frame(self):
        self.main_frame.pack_forget()
        self.genre_frame = tk.Frame(self)
        self.genre_frame.pack(fill='both', expand=True)

        tk.Label(self.genre_frame, text="Select a Genre").pack(pady=5)
        self.genre_var = tk.StringVar(value="science_fiction")
        genres = [
            "science_fiction", "fantasy", "mystery",
            "romance", "history", "horror"
        ]
        genre_menu = ttk.Combobox(self.genre_frame, values=genres, textvariable=self.genre_var, state="readonly")
        genre_menu.pack(pady=5)

        tk.Button(self.genre_frame, text="Search", command=self.find_books).pack(pady=10)
        tk.Button(self.genre_frame, text="Back", command=self.back_to_main).pack(pady=5)

    def find_books(self):
        genre = self.genre_var.get()
        try:
            url = f"https://openlibrary.org/subjects/{genre}.json?limit=15"
            response = requests.get(url)
            data = response.json()
            existing_titles = {book.title for book in self.library.books}

            book_list = []
            for work in data.get("works", []):
                title = work.get("title", "").strip()
                authors = work.get("authors", [])
                if not authors:
                    continue
                author_name = authors[0].get("name", "Unknown").strip()
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
        self.results_frame = tk.Frame(self)
        self.results_frame.pack(fill='both', expand=True)

        tk.Label(self.results_frame, text="Select books to add:").pack()

        checkboxes = []
        for title, author in book_list:
            var = tk.BooleanVar()
            cb = tk.Checkbutton(self.results_frame, text=f"{title} by {author}", variable=var)
            cb.var = var
            cb.title = title
            cb.author = author
            cb.pack(anchor='w')
            checkboxes.append(cb)

        def add_selected_books():
            for cb in checkboxes:
                if cb.var.get():
                    self.library.add_book(Book(cb.title, cb.author))
            self.results_frame.destroy()
            self.back_to_main()

        tk.Button(self.results_frame, text="Add Selected Books", command=add_selected_books).pack(pady=10)
        tk.Button(self.results_frame, text="Back", command=self.return_from_results).pack()

    def return_from_results(self):
        self.results_frame.destroy()
        self.find_books_frame()

    def back_to_main(self):
        if hasattr(self, 'genre_frame'):
            self.genre_frame.destroy()
        self.main_frame.pack(fill='both', expand=True)
        self.refresh_tree()

# Run the App
if __name__ == "__main__":
    app = LibraryApp()
    app.mainloop()
