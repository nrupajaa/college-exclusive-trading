"""
Database helpers for the NHCE Marketplace app (SQLite).
"""
import os
import shutil
import sqlite3
from datetime import datetime

from config import DB_PATH, IMAGE_FOLDER


def init_db():
    os.makedirs("data", exist_ok=True)
    os.makedirs(IMAGE_FOLDER, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS students (
            usn TEXT PRIMARY KEY,
            name TEXT,
            dob TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seller_usn TEXT,
            title TEXT,
            description TEXT,
            price REAL,
            category TEXT,
            image_path TEXT,
            sold_flag INTEGER DEFAULT 0,
            created_at TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS wishlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            buyer_usn TEXT,
            product_id INTEGER
        )
    """)
    # sample account for convenience
    c.execute("SELECT COUNT(*) FROM students WHERE usn = ?", ("1RV17CS001",))
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO students (usn, name, dob) VALUES (?, ?, ?)",
                  ("1RV17CS001", "Test Student", "2000-01-01"))
    conn.commit()
    conn.close()


def add_student(usn, name, dob):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO students (usn, name, dob) VALUES (?, ?, ?)", (usn, name, dob))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return False, "USN already registered."
    conn.close()
    return True, "Registered."


def verify_student(usn, dob):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT name FROM students WHERE usn=? AND dob=?", (usn, dob))
    row = c.fetchone()
    conn.close()
    if row:
        return True, row[0]
    return False, None


def save_product(seller_usn, title, description, price, category, image_src_path):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    image_dest = None
    if image_src_path:
        try:
            ext = os.path.splitext(image_src_path)[1]
            fname = f"{seller_usn}_{int(datetime.now().timestamp())}{ext}"
            image_dest = os.path.join(IMAGE_FOLDER, fname)
            shutil.copy(image_src_path, image_dest)
        except Exception:
            image_dest = None
    created = datetime.now().isoformat()
    c.execute("""INSERT INTO products (seller_usn, title, description, price, category, image_path, created_at)
                 VALUES (?, ?, ?, ?, ?, ?, ?)""",
              (seller_usn, title, description, float(price), category, image_dest, created))
    conn.commit()
    conn.close()


def query_products(search_text=None, category=None, include_sold=False):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    sql = "SELECT id, seller_usn, title, description, price, category, image_path, sold_flag FROM products WHERE 1=1"
    params = []
    if not include_sold:
        sql += " AND sold_flag=0"
    if category and category != "All":
        sql += " AND category=?"
        params.append(category)
    if search_text:
        sql += " AND (title LIKE ? OR description LIKE ?)"
        st = f"%{search_text}%"
        params.extend([st, st])
    sql += " ORDER BY created_at DESC"
    c.execute(sql, params)
    rows = c.fetchall()
    conn.close()
    return rows


def mark_product_sold(product_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE products SET sold_flag=1 WHERE id=?", (product_id,))
    conn.commit()
    conn.close()
    # remove from wishlist if present
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM wishlist WHERE product_id=?", (product_id,))
    conn.commit()
    conn.close()


def add_to_wishlist(buyer_usn, product_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM wishlist WHERE buyer_usn=? AND product_id=?", (buyer_usn, product_id))
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO wishlist (buyer_usn, product_id) VALUES (?, ?)", (buyer_usn, product_id))
        conn.commit()
    conn.close()


def remove_from_wishlist(buyer_usn, product_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM wishlist WHERE buyer_usn=? AND product_id=?", (buyer_usn, product_id))
    conn.commit()
    conn.close()


def get_wishlist(buyer_usn):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""SELECT p.id, p.title, p.price, p.image_path, p.sold_flag FROM products p
                 JOIN wishlist w ON w.product_id = p.id
                 WHERE w.buyer_usn=?""", (buyer_usn,))
    rows = c.fetchall()
    conn.close()
    return rows
