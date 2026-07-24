"""
Tkinter UI for the NHCE Marketplace app.
Contains the main app window (MarketplaceApp) and all page frames.
"""
import os
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False

from config import DB_PATH, XAI_API_KEY
from theme import apply_theme
from database import (
    add_student, verify_student, save_product, query_products,
    mark_product_sold, add_to_wishlist, remove_from_wishlist, get_wishlist,
)
from chat_assistant import is_safe_select, call_grok_api


# ---------------- App ----------------
class MarketplaceApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("NHCE Marketplace")
        self.geometry("1000x650")
        self.resizable(False, False)
        self.current_user = {"usn": None, "name": None}
        self.register_mode = False

        apply_theme(self)

        container = ttk.Frame(self)
        container.pack(fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for F in (LoginPage, RoleSelectionPage, BuyerPage, SellerPage, SellerProductsPage, AddProductPage, WishlistPage, SmartChatPage):
            frame = F(container, self)
            self.frames[F.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("LoginPage")

    def show_frame(self, name):
        frame = self.frames[name]
        frame.tkraise()
        if hasattr(frame, "refresh"):
            frame.refresh()


# ---------------- Pages (UI preserved) ----------------
class LoginPage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        header = ttk.Frame(self)
        header.pack(fill="x", pady=30)
        header.pack_propagate(False)
        header.config(height=80)
        ttk.Label(header, text="NHCE Marketplace", style="Heading.TLabel").pack(anchor="center")

        panel = ttk.Frame(self, style="Card.TFrame")
        panel.place(relx=0.5, rely=0.5, anchor="center", width=560, height=260)

        form = ttk.Frame(panel, style="Card.TFrame")
        form.place(relx=0.5, rely=0.5, anchor="center")

        ttk.Label(form, text="STUDENT LOGIN", font=("Julius Sans One", 18, "bold"),
                  background="#EDEDED", foreground="#333333").grid(row=0, column=0, columnspan=2, pady=(0, 10))

        ttk.Label(form, text="USN:", style="Small.TLabel", background="#EDEDED", foreground="#333333").grid(row=1, column=0, sticky="e", padx=8, pady=6)
        self.usn_entry = ttk.Entry(form, width=34, style="TEntry")
        self.usn_entry.grid(row=1, column=1, padx=8, pady=6)

        ttk.Label(form, text="D.O.B:", style="Small.TLabel", background="#EDEDED", foreground="#333333").grid(row=2, column=0, sticky="e", padx=8, pady=6)
        self.dob_entry = ttk.Entry(form, width=34, style="TEntry")
        self.dob_entry.grid(row=2, column=1, padx=8, pady=6)

        # Name fields for register (hidden initially)
        self.name_label = ttk.Label(form, text="Name:", style="Small.TLabel", background="#EDEDED", foreground="#333333")
        self.name_entry = ttk.Entry(form, width=34, style="TEntry")

        btn_row = ttk.Frame(form, style="Card.TFrame")
        btn_row.grid(row=5, column=0, columnspan=2, pady=(12, 4))
        self.login_btn = ttk.Button(btn_row, text="Login", command=self.do_login, width=16)
        self.login_btn.grid(row=0, column=0, padx=6)
        self.toggle_btn = ttk.Button(btn_row, text="Register (New Student)", command=self.toggle_mode, width=20)
        self.toggle_btn.grid(row=0, column=1, padx=6)

    def toggle_mode(self):
        self.controller.register_mode = not self.controller.register_mode
        if self.controller.register_mode:
            self.name_label.grid(row=3, column=0, sticky="e", padx=8, pady=6)
            self.name_entry.grid(row=3, column=1, padx=8, pady=6)
            self.login_btn.config(text="Register", command=self.do_register)
            self.toggle_btn.config(text="Back to Login")
        else:
            self.name_label.grid_remove()
            self.name_entry.grid_remove()
            self.login_btn.config(text="Login", command=self.do_login)
            self.toggle_btn.config(text="Register (New Student)")

    def do_login(self):
        usn = self.usn_entry.get().strip()
        dob = self.dob_entry.get().strip()
        if not usn or not dob:
            messagebox.showwarning("Missing", "Enter both USN and DOB")
            return
        ok, name = verify_student(usn, dob)
        if ok:
            self.controller.current_user["usn"] = usn
            self.controller.current_user["name"] = name
            messagebox.showinfo("Welcome", f"Welcome {name} ({usn})")
            self.controller.show_frame("RoleSelectionPage")
        else:
            messagebox.showerror("Login failed", "No matching student found. Please register or check details.")

    def do_register(self):
        usn = self.usn_entry.get().strip()
        name = self.name_entry.get().strip()
        dob = self.dob_entry.get().strip()
        if not (usn and name and dob):
            messagebox.showwarning("Missing", "Fill all fields")
            return
        ok, msg = add_student(usn, name, dob)
        if ok:
            messagebox.showinfo("Success", "Registered successfully. Please login.")
            self.toggle_mode()
        else:
            messagebox.showerror("Error", msg)


class RoleSelectionPage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        top = ttk.Frame(self)
        top.pack(fill="x", pady=30)
        ttk.Label(top, text="WELCOME", style="Heading.TLabel").pack(anchor="w", padx=30)

        self.welcome_lbl = ttk.Label(self, text="", font=("Julius Sans One", 14))
        self.welcome_lbl.pack(anchor="w", padx=30, pady=(4, 20))

        center = ttk.Frame(self)
        center.pack(expand=True)
        left_btn = ttk.Button(center, text="BUY", command=lambda: controller.show_frame("BuyerPage"), width=22)
        left_btn.grid(row=0, column=0, padx=50, pady=20)
        right_btn = ttk.Button(center, text="SELL", command=lambda: controller.show_frame("SellerPage"), width=22)
        right_btn.grid(row=0, column=1, padx=50, pady=20)

        bottom = ttk.Frame(self)
        bottom.pack(fill="x", pady=20)
        ttk.Button(bottom, text="Logout", command=self.logout).pack(anchor="e", padx=30)

    def refresh(self):
        name = self.controller.current_user.get("name") or ""
        usn = self.controller.current_user.get("usn") or ""
        self.welcome_lbl.config(text=f"{name} ({usn})")

    def logout(self):
        self.controller.current_user = {"usn": None, "name": None}
        self.controller.show_frame("LoginPage")


class BuyerPage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self._photo_cache = {}

        # HEADER
        header = ttk.Frame(self)
        header.pack(fill="x", pady=12)
        ttk.Label(header, text="SHOP", style="Heading.TLabel").pack(anchor="w", padx=20)

        # CONTROLS
        controls = ttk.Frame(self)
        controls.pack(fill="x", padx=20, pady=(6, 10))

        ttk.Label(controls, text="Search:", font=("Julius Sans One", 10)).pack(side="left")
        self.search_var = tk.StringVar()
        ttk.Entry(controls, textvariable=self.search_var, width=28, style="TEntry").pack(side="left", padx=8)

        ttk.Label(controls, text="Category:", font=("Julius Sans One", 10)).pack(side="left", padx=(12, 4))
        self.cat_var = tk.StringVar(value="All")
        cats = ["All", "Books", "Notes", "Furniture", "Electronics", "Other"]
        self.cat_combo = ttk.Combobox(controls, values=cats, textvariable=self.cat_var, width=14)
        self.cat_combo.pack(side="left")

        ttk.Button(controls, text="Apply", command=self.refresh).pack(side="left", padx=8)

        # Right-side buttons
        ttk.Button(controls, text="Chat Assistant \U0001F916",
                   command=lambda: controller.show_frame("SmartChatPage")).pack(side="right", padx=6)

        ttk.Button(controls, text="Wishlist",
                   command=lambda: controller.show_frame("WishlistPage")).pack(side="right", padx=6)

        list_frame = ttk.Frame(self)
        list_frame.pack(fill="both", expand=True, padx=20, pady=(6, 20))

        self.canvas = tk.Canvas(list_frame, bg="#7C9BA3", highlightthickness=0)
        self.scroll_frame = ttk.Frame(self.canvas)

        vsb = ttk.Scrollbar(list_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=vsb.set)

        vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.scroll_frame.bind("<Configure>", self.on_frame_configure)

        bottom_bar = ttk.Frame(self)
        bottom_bar.pack(fill="x", side="bottom", pady=10, padx=20)

        ttk.Button(
            bottom_bar,
            text="Back",
            command=lambda: controller.show_frame("RoleSelectionPage")
        ).pack(side="right")

    def on_frame_configure(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def refresh(self):
        for w in self.scroll_frame.winfo_children():
            w.destroy()
        search = self.search_var.get().strip()
        cat = self.cat_var.get()
        rows = query_products(search_text=search, category=cat, include_sold=False)
        if not rows:
            ttk.Label(self.scroll_frame, text="No products found.", font=("Julius Sans One", 12), background="#7C9BA3").pack(pady=20)
            return
        for row in rows:
            pid, seller_usn, title, desc, price, category, image_path, sold_flag = row
            card = ttk.Frame(self.scroll_frame, style="Card.TFrame")
            card.pack(fill="x", pady=10, padx=6)
            left = ttk.Frame(card, style="Card.TFrame", width=120)
            left.pack(side="left", padx=8, pady=8)
            if image_path and os.path.exists(image_path) and PIL_AVAILABLE:
                try:
                    img = Image.open(image_path).resize((120, 80))
                    photo = ImageTk.PhotoImage(img)
                    lbl = tk.Label(left, image=photo, bg="#EDEDED")
                    lbl.image = photo
                    lbl.pack()
                except Exception:
                    ttk.Label(left, text="No Image", background="#EDEDED").pack()
            else:
                ttk.Label(left, text="No Image", background="#EDEDED").pack(ipadx=12, ipady=12)

            right = ttk.Frame(card, style="Card.TFrame")
            right.pack(side="left", fill="both", expand=True, padx=8, pady=8)
            ttk.Label(right, text=f"{title}", font=("Julius Sans One", 12, "bold"), background="#EDEDED", foreground="#111111").pack(anchor="w")
            ttk.Label(right, text=f"Category: {category}  |  Price: \u20b9{price}", background="#EDEDED", foreground="#333333").pack(anchor="w", pady=(4, 0))
            ttk.Label(right, text=f"By: {seller_usn}", background="#EDEDED", foreground="#555555").pack(anchor="w", pady=(4, 6))
            ttk.Label(right, text=f"{desc}", wraplength=600, background="#EDEDED", foreground="#333333").pack(anchor="w", pady=(0, 6))

            btn_row = ttk.Frame(right, style="Card.TFrame")
            btn_row.pack(anchor="e")
            ttk.Button(btn_row, text="Add to Wishlist", command=lambda pid=pid: self.add_to_wishlist(pid)).grid(row=0, column=0, padx=6)
            ttk.Button(btn_row, text="Buy", command=lambda pid=pid: self.buy_product(pid)).grid(row=0, column=1, padx=6)

    def add_to_wishlist(self, pid):
        buyer = self.controller.current_user.get("usn")
        if not buyer:
            messagebox.showwarning("Login required", "Please login first.")
            return
        add_to_wishlist(buyer, pid)
        messagebox.showinfo("Wishlist", "Added to wishlist.")

    def buy_product(self, pid):
        ans = messagebox.askyesno("Confirm", "Do you want to buy this product? This will mark it as sold.")
        if not ans:
            return
        mark_product_sold(pid)
        messagebox.showinfo("Purchased", "Purchase successful! Product marked as sold.")
        self.refresh()
        self.controller.frames["SellerProductsPage"].refresh()
        if "WishlistPage" in self.controller.frames:
            self.controller.frames["WishlistPage"].refresh()


class SellerPage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        header = ttk.Frame(self)
        header.pack(fill="x", pady=12)
        ttk.Label(header, text="SELL YOUR PRODUCT", style="Heading.TLabel").pack(anchor="w", padx=20)

        controls = ttk.Frame(self)
        controls.pack(fill="x", padx=20, pady=(6, 10))
        ttk.Button(controls, text="ADD PRODUCT", command=lambda: controller.show_frame("AddProductPage")).pack(side="left")
        ttk.Button(controls, text="My Products", command=lambda: controller.show_frame("SellerProductsPage")).pack(side="left", padx=8)
        # Chat Assistant button added
        ttk.Button(controls, text="Chat Assistant \U0001F916", command=lambda: controller.show_frame("SmartChatPage")).pack(side="left", padx=8)
        ttk.Button(controls, text="Back", command=lambda: controller.show_frame("RoleSelectionPage")).pack(side="right")


class SellerProductsPage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        header = ttk.Frame(self)
        header.pack(fill="x", pady=12)
        ttk.Label(header, text="YOUR PRODUCTS", style="Heading.TLabel").pack(side="left", padx=20)
        ttk.Button(header, text="Back", command=lambda: controller.show_frame("RoleSelectionPage")).pack(side="right", padx=20)

        container = ttk.Frame(self)
        container.pack(fill="both", expand=True, padx=20, pady=10)

        self.canvas = tk.Canvas(container, bg="#7C9BA3", highlightthickness=0)
        self.scroll_frame = ttk.Frame(self.canvas)
        vsb = ttk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.scroll_frame.bind("<Configure>", self.on_frame_configure)

    def on_frame_configure(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def refresh(self):
        for w in self.scroll_frame.winfo_children():
            w.destroy()
        usn = self.controller.current_user.get("usn")
        if not usn:
            ttk.Label(self.scroll_frame, text="No seller selected.", background="#7C9BA3").pack()
            return
        rows = query_products(include_sold=True)
        seller_rows = [r for r in rows if r[1] == usn]
        if not seller_rows:
            ttk.Label(self.scroll_frame, text="You haven't listed any products yet.", background="#7C9BA3").pack(pady=20)
            return
        for row in seller_rows:
            pid, seller_usn, title, desc, price, category, image_path, sold_flag = row
            card = ttk.Frame(self.scroll_frame, style="Card.TFrame")
            card.pack(fill="x", pady=8, padx=6)
            left = ttk.Frame(card, style="Card.TFrame", width=120)
            left.pack(side="left", padx=8, pady=8)
            if image_path and os.path.exists(image_path) and PIL_AVAILABLE:
                try:
                    img = Image.open(image_path).resize((120, 80))
                    photo = ImageTk.PhotoImage(img)
                    lbl = tk.Label(left, image=photo, bg="#EDEDED")
                    lbl.image = photo
                    lbl.pack()
                except Exception:
                    ttk.Label(left, text="No Image", background="#EDEDED").pack()
            else:
                ttk.Label(left, text="No Image", background="#EDEDED").pack(ipadx=12, ipady=12)

            right = ttk.Frame(card, style="Card.TFrame")
            right.pack(side="left", fill="both", expand=True, padx=8, pady=8)
            ttk.Label(right, text=f"{title}", font=("Julius Sans One", 12, "bold"), background="#EDEDED", foreground="#111111").pack(anchor="w")
            ttk.Label(right, text=f"Category: {category} | Price: \u20b9{price}", background="#EDEDED", foreground="#333333").pack(anchor="w")
            ttk.Label(right, text=f"{desc}", wraplength=700, background="#EDEDED", foreground="#333333").pack(anchor="w", pady=(4, 6))
            status = "SOLD" if sold_flag else "Available"
            ttk.Label(right, text=f"Status: {status}", background="#EDEDED", foreground=("#990000" if sold_flag else "#116611")).pack(anchor="w")
            btn_row = ttk.Frame(right)
            btn_row.pack(anchor="e", pady=4)
            if not sold_flag:
                ttk.Button(btn_row, text="Mark Sold", command=lambda pid=pid: self.mark_sold(pid)).pack()

    def mark_sold(self, pid):
        mark_product_sold(pid)
        messagebox.showinfo("Marked", "Product marked as sold.")
        self.refresh()
        if "BuyerPage" in self.controller.frames:
            self.controller.frames["BuyerPage"].refresh()
        if "WishlistPage" in self.controller.frames:
            self.controller.frames["WishlistPage"].refresh()


class AddProductPage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        header = ttk.Frame(self)
        header.pack(fill="x", pady=12)
        ttk.Label(header, text="ADD NEW PRODUCT", style="Heading.TLabel").pack(anchor="w", padx=20)

        panel = ttk.Frame(self, style="Card.TFrame")
        panel.place(relx=0.5, rely=0.55, anchor="center", width=840, height=360)

        form = ttk.Frame(panel, style="Card.TFrame")
        form.place(relx=0.5, rely=0.5, anchor="center")

        ttk.Label(form, text="Title:", background="#EDEDED", foreground="#333333").grid(row=0, column=0, sticky="e", padx=8, pady=6)
        self.title_entry = ttk.Entry(form, width=60)
        self.title_entry.grid(row=0, column=1, pady=6, sticky="w")

        ttk.Label(form, text="Category:", background="#EDEDED", foreground="#333333").grid(row=1, column=0, sticky="e", padx=8, pady=6)
        self.cat = ttk.Combobox(form, values=["Books", "Notes", "Furniture", "Electronics", "Other"], width=20)
        self.cat.grid(row=1, column=1, sticky="w", pady=6)

        ttk.Label(form, text="Price (INR):", background="#EDEDED", foreground="#333333").grid(row=2, column=0, sticky="e", padx=8, pady=6)
        self.price_entry = ttk.Entry(form, width=20)
        self.price_entry.grid(row=2, column=1, sticky="w", pady=6)

        ttk.Label(form, text="Description:", background="#EDEDED", foreground="#333333").grid(row=3, column=0, sticky="ne", padx=8, pady=6)
        self.desc_text = tk.Text(form, width=60, height=6)
        self.desc_text.grid(row=3, column=1, pady=6, sticky="w")

        ttk.Label(form, text="Photo:", background="#EDEDED", foreground="#333333").grid(row=4, column=0, sticky="e", padx=8, pady=6)
        path_frame = ttk.Frame(form)
        path_frame.grid(row=4, column=1, sticky="w")
        self.photo_var = tk.StringVar()
        ttk.Entry(path_frame, textvariable=self.photo_var, width=50).pack(side="left")
        ttk.Button(path_frame, text="Browse", command=self.browse_photo).pack(side="left", padx=6)

        action_row = ttk.Frame(form)
        action_row.grid(row=5, column=0, columnspan=2, pady=12)
        ttk.Button(action_row, text="Add Product", command=self.save_product).pack(side="left", padx=6)
        ttk.Button(action_row, text="Back", command=lambda: controller.show_frame("SellerPage")).pack(side="left", padx=6)

    def browse_photo(self):
        p = filedialog.askopenfilename(title="Select Image", filetypes=[("Images", "*.png *.jpg *.jpeg *.gif")])
        if p:
            self.photo_var.set(p)

    def save_product(self):
        title = self.title_entry.get().strip()
        category = self.cat.get().strip()
        price = self.price_entry.get().strip()
        desc = self.desc_text.get("1.0", "end").strip()
        photo = self.photo_var.get().strip()
        if not title or not price:
            messagebox.showwarning("Missing", "Enter both title and price.")
            return
        try:
            float(price)
        except ValueError:
            messagebox.showwarning("Invalid", "Price must be numeric.")
            return
        seller_usn = self.controller.current_user.get("usn")
        save_product(seller_usn, title, desc, price, category or "Other", photo)
        messagebox.showinfo("Saved", "Product added successfully.")
        self.title_entry.delete(0, "end")
        self.price_entry.delete(0, "end")
        self.desc_text.delete("1.0", "end")
        self.photo_var.set("")
        self.cat.set("")
        self.controller.show_frame("SellerProductsPage")
        self.controller.frames["SellerProductsPage"].refresh()


class WishlistPage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self._photo_cache = {}

        header = ttk.Frame(self)
        header.pack(fill="x", pady=12)
        ttk.Label(header, text="MY WISHLIST", style="Heading.TLabel").pack(anchor="w", padx=20)

        controls = ttk.Frame(self)
        controls.pack(fill="x", padx=20, pady=(6, 10))
        ttk.Button(controls, text="Back", command=lambda: controller.show_frame("BuyerPage")).pack(side="right")
        ttk.Label(controls, text="Your wishlist items are shown below.", font=("Julius Sans One", 10)).pack(side="left")

        container = ttk.Frame(self)
        container.pack(fill="both", expand=True, padx=20, pady=6)

        self.canvas = tk.Canvas(container, bg="#7C9BA3", highlightthickness=0)
        self.scroll_frame = ttk.Frame(self.canvas)
        vsb = ttk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.scroll_frame.bind("<Configure>", self.on_frame_configure)

    def on_frame_configure(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def refresh(self):
        for w in self.scroll_frame.winfo_children():
            w.destroy()
        buyer = self.controller.current_user.get("usn")
        if not buyer:
            ttk.Label(self.scroll_frame, text="Please login to view wishlist.", background="#7C9BA3").pack(pady=20)
            return
        rows = get_wishlist(buyer)
        if not rows:
            ttk.Label(self.scroll_frame, text="Your wishlist is empty.", background="#7C9BA3").pack(pady=20)
            return
        for pid, title, price, image_path, sold_flag in rows:
            card = ttk.Frame(self.scroll_frame, style="Card.TFrame")
            card.pack(fill="x", pady=8, padx=6)
            left = ttk.Frame(card, style="Card.TFrame", width=120)
            left.pack(side="left", padx=8, pady=8)
            if image_path and os.path.exists(image_path) and PIL_AVAILABLE:
                try:
                    img = Image.open(image_path).resize((120, 80))
                    photo = ImageTk.PhotoImage(img)
                    lbl = tk.Label(left, image=photo, bg="#EDEDED")
                    lbl.image = photo
                    lbl.pack()
                except Exception:
                    ttk.Label(left, text="No Image", background="#EDEDED").pack()
            else:
                ttk.Label(left, text="No Image", background="#EDEDED").pack(ipadx=12, ipady=12)

            right = ttk.Frame(card, style="Card.TFrame")
            right.pack(side="left", fill="both", expand=True, padx=8, pady=8)
            ttk.Label(right, text=f"{title}", font=("Julius Sans One", 12, "bold"), background="#EDEDED", foreground="#111111").pack(anchor="w")
            ttk.Label(right, text=f"Price: \u20b9{price}", background="#EDEDED", foreground="#333333").pack(anchor="w", pady=(4, 6))
            status_text = "SOLD" if sold_flag else "Available"
            ttk.Label(right, text=f"Status: {status_text}", background="#EDEDED", foreground=("#990000" if sold_flag else "#116611")).pack(anchor="w")
            btn_row = ttk.Frame(right)
            btn_row.pack(anchor="e", pady=6)
            if not sold_flag:
                ttk.Button(btn_row, text="Buy", command=lambda pid=pid: self.buy_from_wishlist(pid)).grid(row=0, column=0, padx=6)
            ttk.Button(btn_row, text="Remove", command=lambda pid=pid: self.remove_item(pid)).grid(row=0, column=1, padx=6)

    def buy_from_wishlist(self, pid):
        ans = messagebox.askyesno("Confirm", "Proceed to buy this item? This will mark it as sold.")
        if not ans:
            return
        mark_product_sold(pid)
        messagebox.showinfo("Purchased", "Successfully purchased. Item marked as sold.")
        self.refresh()
        if "BuyerPage" in self.controller.frames:
            self.controller.frames["BuyerPage"].refresh()
        if "SellerProductsPage" in self.controller.frames:
            self.controller.frames["SellerProductsPage"].refresh()

    def remove_item(self, pid):
        buyer = self.controller.current_user.get("usn")
        if not buyer:
            return
        remove_from_wishlist(buyer, pid)
        messagebox.showinfo("Removed", "Item removed from wishlist.")
        self.refresh()


# ---------------- Smart Chat Page (Grok) ----------------
class SmartChatPage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.configure(style="Content.TFrame", padding=12)

        ttk.Label(self, text="NHCE Marketplace Smart Assistant \U0001F916", font=("Julius Sans One", 20, "bold"), background="#7C9BA3").pack(pady=12)

        self.chat_box = tk.Text(self, width=88, height=18, wrap="word", state="disabled", bg="#F5F5F5")
        self.chat_box.pack(padx=12, pady=6)

        entry_frame = ttk.Frame(self)
        entry_frame.pack(pady=6)
        self.user_entry = ttk.Entry(entry_frame, width=70)
        self.user_entry.pack(side="left", padx=6)
        ttk.Button(entry_frame, text="Send", command=self.process_input).pack(side="left", padx=6)
        # small note about API key if missing
        ttk.Button(self, text="Back", command=lambda: controller.show_frame("RoleSelectionPage")).pack(pady=8)

    def add_message(self, sender, msg):
        self.chat_box.config(state="normal")
        self.chat_box.insert(tk.END, f"{sender}: {msg}\n\n")
        self.chat_box.config(state="disabled")
        self.chat_box.see(tk.END)

    def process_input(self):
        question = self.user_entry.get().strip()
        if not question:
            return
        self.add_message("You", question)
        # thinking indicator
        self.add_message("Bot", "Thinking...")
        self.update_idletasks()
        answer = self.answer_question(question)
        # remove thinking
        self.chat_box.config(state="normal")
        content = self.chat_box.get("1.0", tk.END).rstrip("\n")
        idx = content.rfind("Bot: Thinking...")
        if idx != -1:
            new_content = content[:idx].rstrip("\n") + "\n\n"
            self.chat_box.delete("1.0", tk.END)
            self.chat_box.insert(tk.END, new_content)
            self.chat_box.config(state="disabled")
        self.add_message("Bot", answer)
        self.user_entry.delete(0, tk.END)

    def answer_question(self, question: str) -> str:
        qlow = question.lower()

        # Direct rule-based answers for the four specific types:
        # 1) trending / most popular category
        if "trending" in qlow or "most popular" in qlow or ("most" in qlow and "sold" in qlow) or "most bought" in qlow:
            try:
                conn = sqlite3.connect(DB_PATH)
                cur = conn.cursor()
                cur.execute("SELECT category, COUNT(*) AS sales FROM products WHERE sold_flag=1 GROUP BY category ORDER BY sales DESC LIMIT 1")
                row = cur.fetchone()
                conn.close()
                if not row:
                    return "No sales data yet."
                return f"Trending category: {row[0]} ({row[1]} sold)."
            except Exception as e:
                return f"SQL error while computing trending: {e}"

        # 2) least bought (category or product with smallest sold count)
        if "least bought" in qlow or "least purchased" in qlow or ("least" in qlow and "bought" in qlow):
            try:
                conn = sqlite3.connect(DB_PATH)
                cur = conn.cursor()
                # group by title to find product with the smallest number of sold instances
                cur.execute("SELECT title, COUNT(*) as sold_count FROM products WHERE sold_flag=1 GROUP BY title ORDER BY sold_count ASC LIMIT 1")
                row = cur.fetchone()
                conn.close()
                if not row:
                    return "No sales/purchase records yet to determine least bought product."
                return f"The least bought product (by sold instances) is '{row[0]}' with {row[1]} sales."
            except Exception as e:
                return f"SQL error while computing least-bought: {e}"

        # 3) cheapest
        if "cheapest" in qlow or "least expensive" in qlow or ("lowest price" in qlow):
            try:
                conn = sqlite3.connect(DB_PATH)
                cur = conn.cursor()
                cur.execute("SELECT title, price FROM products WHERE price IS NOT NULL ORDER BY price ASC LIMIT 1")
                row = cur.fetchone()
                conn.close()
                if not row:
                    return "No products with price available."
                return f"The cheapest product is '{row[0]}' priced at \u20b9{row[1]}."
            except Exception as e:
                return f"SQL error while finding cheapest: {e}"

        # 4) most expensive
        if "most expensive" in qlow or "costliest" in qlow or ("highest price" in qlow):
            try:
                conn = sqlite3.connect(DB_PATH)
                cur = conn.cursor()
                cur.execute("SELECT title, price FROM products WHERE price IS NOT NULL ORDER BY price DESC LIMIT 1")
                row = cur.fetchone()
                conn.close()
                if not row:
                    return "No products with price available."
                return f"The most expensive product is '{row[0]}' priced at \u20b9{row[1]}."
            except Exception as e:
                return f"SQL error while finding most expensive: {e}"

        # other common quick stats
        if "how many" in qlow and ("unsold" in qlow or "available" in qlow or "available products" in qlow):
            try:
                conn = sqlite3.connect(DB_PATH)
                cur = conn.cursor()
                cur.execute("SELECT COUNT(*) FROM products WHERE sold_flag=0")
                r = cur.fetchone()
                conn.close()
                return f"There are {r[0]} unsold products available."
            except Exception as e:
                return f"SQL error: {e}"

        # If no Grok API key, fallback to local rule-based answers
        if not (XAI_API_KEY or os.getenv("XAI_API_KEY")):
            return self.fallback_answer(question)

        # Otherwise attempt to ask Grok to generate a safe SELECT
        prompt = (
            "You are an SQL generator. Output only a single valid SQLite SELECT statement (no explanation). "
            "Use ONLY this table: products with columns: id, title, price, category, seller_usn, sold_flag, description, image_path, created_at. "
            "Do NOT use aliases like t1 or p, do not invent columns, do not include semicolons or multiple statements. "
            f"Question: \"{question}\""
        )

        ok, sql_or_err = call_grok_api(prompt, max_tokens=180)
        if not ok:
            return f"Grok API error: {sql_or_err}"

        sql_text = (sql_or_err or "").strip()
        if "select" in sql_text.lower():
            low = sql_text.lower()
            idx = low.find("select")
            sql_text = sql_text[idx:]
            sql_text = sql_text.strip().strip("`\"'")
        else:
            return f"Grok did not return a SELECT statement. Raw response:\n{sql_or_err}"

        if not is_safe_select(sql_text):
            return f"Generated SQL was unsafe or used unknown columns. Generated SQL:\n{sql_text}"

        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute(sql_text)
            rows = cur.fetchall()
            conn.close()
        except Exception as e:
            return f"SQL execution error: {e}\nGenerated SQL:\n{sql_text}"

        db_result = "No results." if not rows else f"{len(rows)} rows. Preview: {rows[:8]}"

        final_prompt = (
            "Convert the database result into a concise conversational answer for the user.\n"
            f"User question: {question}\n"
            f"Database result: {db_result}\n"
            "Answer in 2-3 sentences."
        )
        ok2, resp_text = call_grok_api(final_prompt, max_tokens=200)
        if ok2:
            return (resp_text or db_result).strip()
        else:
            return db_result

    def fallback_answer(self, question: str) -> str:
        q = question.lower()
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            if "trending" in q or "popular" in q or "most sold" in q:
                c.execute("SELECT category, COUNT(*) as sold_count FROM products WHERE sold_flag=1 GROUP BY category ORDER BY sold_count DESC LIMIT 1")
                r = c.fetchone()
                conn.close()
                if r:
                    return f"The most trending category right now is '{r[0]}' with {r[1]} items sold."
                return "No sales data available yet."
            if "most bought" in q or "most purchased" in q:
                c.execute("SELECT title, COUNT(*) as sold_count FROM products WHERE sold_flag=1 GROUP BY title ORDER BY sold_count DESC LIMIT 1")
                r = c.fetchone()
                conn.close()
                if r:
                    return f"The most bought product is '{r[0]}' with {r[1]} sales."
                return "No purchase data available."
            if "least bought" in q or "least purchased" in q:
                c.execute("SELECT title, COUNT(*) as sold_count FROM products WHERE sold_flag=1 GROUP BY title ORDER BY sold_count ASC LIMIT 1")
                r = c.fetchone()
                conn.close()
                if r:
                    return f"The least bought product is '{r[0]}' with {r[1]} sales."
                return "No purchase data available."
            if "cheapest" in q or "least expensive" in q or "lowest price" in q:
                c.execute("SELECT title, price FROM products WHERE price IS NOT NULL ORDER BY price ASC LIMIT 1")
                r = c.fetchone()
                conn.close()
                if r:
                    return f"The cheapest product is '{r[0]}' priced at \u20b9{r[1]}."
                return "No priced products available."
            if "most expensive" in q or "costliest" in q or "highest price" in q:
                c.execute("SELECT title, price FROM products WHERE price IS NOT NULL ORDER BY price DESC LIMIT 1")
                r = c.fetchone()
                conn.close()
                if r:
                    return f"The most expensive product is '{r[0]}' priced at \u20b9{r[1]}."
                return "No priced products available."
            if "available" in q or "unsold" in q or "how many" in q:
                c.execute("SELECT COUNT(*) FROM products WHERE sold_flag=0")
                r = c.fetchone()
                conn.close()
                return f"There are {r[0]} unsold products currently."
            conn.close()
        except Exception as e:
            return f"Error reading database: {e}"
        return "Sorry, I couldn't understand. Try questions like 'Which category is trending?', 'Which product is cheapest?', 'Which product is most expensive?', or 'Which product is least bought?'"
