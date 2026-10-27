from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "inventory.db"

app = Flask(__name__)
app.secret_key = "change-this-secret-key-for-production"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                sku TEXT NOT NULL UNIQUE,
                category TEXT NOT NULL DEFAULT 'General',
                quantity INTEGER NOT NULL DEFAULT 0 CHECK(quantity >= 0),
                price REAL NOT NULL DEFAULT 0 CHECK(price >= 0),
                supplier TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL
            )
        """)
        count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        if count == 0:
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            demo = [
                ("Wireless Mouse", "ELE-001", "Electronics", 24, 599.00, "Tech Supplies"),
                ("Notebook A5", "STA-002", "Stationery", 8, 65.00, "Paper House"),
                ("USB-C Cable", "ELE-003", "Electronics", 5, 249.00, "Tech Supplies"),
                ("Desk Organizer", "OFF-004", "Office", 0, 349.00, "Office Mart"),
            ]
            conn.executemany(
                "INSERT INTO products (name, sku, category, quantity, price, supplier, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                [row + (now,) for row in demo]
            )


@app.template_filter("inr")
def inr(value):
    return f"₹{float(value or 0):,.2f}"


@app.route("/")
def dashboard():
    search = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    conn = get_db()
    stats = {
        "products": conn.execute("SELECT COUNT(*) FROM products").fetchone()[0],
        "units": conn.execute("SELECT COALESCE(SUM(quantity), 0) FROM products").fetchone()[0],
        "value": conn.execute("SELECT COALESCE(SUM(quantity * price), 0) FROM products").fetchone()[0],
        "low_stock": conn.execute("SELECT COUNT(*) FROM products WHERE quantity > 0 AND quantity <= 10").fetchone()[0],
        "out_stock": conn.execute("SELECT COUNT(*) FROM products WHERE quantity = 0").fetchone()[0],
    }
    categories = [r["category"] for r in conn.execute("SELECT DISTINCT category FROM products ORDER BY category")]
    sql = "SELECT * FROM products WHERE (name LIKE ? OR sku LIKE ? OR supplier LIKE ?)"
    args = [f"%{search}%"] * 3
    if category:
        sql += " AND category = ?"
        args.append(category)
    sql += " ORDER BY CASE WHEN quantity = 0 THEN 0 WHEN quantity <= 10 THEN 1 ELSE 2 END, name"
    products = conn.execute(sql, args).fetchall()
    conn.close()
    return render_template("dashboard.html", stats=stats, products=products, categories=categories, q=search, selected_category=category)


@app.route("/products/new", methods=["GET", "POST"])
def add_product():
    if request.method == "POST":
        data = product_form_data()
        error = validate_product(data)
        if error:
            flash(error, "error")
            return render_template("product_form.html", product=data, mode="Add")
        try:
            with get_db() as conn:
                conn.execute(
                    "INSERT INTO products (name, sku, category, quantity, price, supplier, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (data["name"], data["sku"], data["category"], data["quantity"], data["price"], data["supplier"], datetime.now().strftime("%Y-%m-%d %H:%M"))
                )
            flash("Product added successfully.", "success")
            return redirect(url_for("dashboard"))
        except sqlite3.IntegrityError:
            flash("That SKU already exists. Please use a unique SKU.", "error")
            return render_template("product_form.html", product=data, mode="Add")
    return render_template("product_form.html", product={}, mode="Add")


@app.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
def edit_product(product_id):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if not row:
        flash("Product not found.", "error")
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        data = product_form_data()
        error = validate_product(data)
        if error:
            flash(error, "error")
            return render_template("product_form.html", product=data, mode="Edit", product_id=product_id)
        try:
            with get_db() as conn:
                conn.execute(
                    "UPDATE products SET name=?, sku=?, category=?, quantity=?, price=?, supplier=?, updated_at=? WHERE id=?",
                    (data["name"], data["sku"], data["category"], data["quantity"], data["price"], data["supplier"], datetime.now().strftime("%Y-%m-%d %H:%M"), product_id)
                )
            flash("Product updated successfully.", "success")
            return redirect(url_for("dashboard"))
        except sqlite3.IntegrityError:
            flash("That SKU is already used by another product.", "error")
            return render_template("product_form.html", product=data, mode="Edit", product_id=product_id)
    return render_template("product_form.html", product=dict(row), mode="Edit", product_id=product_id)


@app.route("/products/<int:product_id>/delete", methods=["POST"])
def delete_product(product_id):
    with get_db() as conn:
        conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
    flash("Product deleted.", "success")
    return redirect(url_for("dashboard"))


@app.route("/products/<int:product_id>/stock", methods=["POST"])
def update_stock(product_id):
    action = request.form.get("action")
    try:
        amount = int(request.form.get("amount", "0"))
        if amount <= 0:
            raise ValueError
    except ValueError:
        flash("Enter a whole number greater than zero.", "error")
        return redirect(url_for("dashboard"))
    with get_db() as conn:
        product = conn.execute("SELECT quantity FROM products WHERE id=?", (product_id,)).fetchone()
        if not product:
            flash("Product not found.", "error")
        elif action == "remove" and amount > product["quantity"]:
            flash("Cannot remove more units than are currently in stock.", "error")
        elif action not in ("add", "remove"):
            flash("Invalid stock action.", "error")
        else:
            new_quantity = product["quantity"] + amount if action == "add" else product["quantity"] - amount
            conn.execute("UPDATE products SET quantity=?, updated_at=? WHERE id=?",
                         (new_quantity, datetime.now().strftime("%Y-%m-%d %H:%M"), product_id))
            flash("Stock updated.", "success")
    return redirect(url_for("dashboard"))


def product_form_data():
    form = request.form
    try:
        quantity = int(form.get("quantity", "0"))
    except ValueError:
        quantity = -1
    try:
        price = float(form.get("price", "0"))
    except ValueError:
        price = -1
    return {
        "name": form.get("name", "").strip(),
        "sku": form.get("sku", "").strip().upper(),
        "category": form.get("category", "General").strip() or "General",
        "quantity": quantity,
        "price": price,
        "supplier": form.get("supplier", "").strip(),
    }


def validate_product(data):
    if not data["name"] or not data["sku"]:
        return "Product name and SKU are required."
    if data["quantity"] < 0:
        return "Quantity must be a whole number zero or higher."
    if data["price"] < 0:
        return "Price must be zero or higher."
    if len(data["sku"]) > 40:
        return "SKU must be 40 characters or fewer."
    return None


@app.route("/health")
def health():
    return {"status": "ok"}


# Initialize the SQLite database both locally and when hosted by a WSGI server.
init_db()

if __name__ == "__main__":
    app.run(debug=False)
