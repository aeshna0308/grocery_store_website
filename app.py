import os
import sqlite3
import secrets
from functools import wraps
from pathlib import Path

from flask import (
    Flask, render_template, request, redirect, url_for, session,
    flash, abort
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "grocery.db"
UPLOAD_DIR = BASE_DIR / "static" / "uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-before-deploying")
app.config["MAX_CONTENT_LENGTH"] = MAX_IMAGE_SIZE
app.config["UPLOAD_FOLDER"] = str(UPLOAD_DIR)

# Change these before putting the site online.
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "ChangeMe123!")

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with get_db() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            category TEXT DEFAULT '',
            unit TEXT DEFAULT '1 piece',
            price REAL NOT NULL,
            discount_price REAL,
            image TEXT DEFAULT '',
            stock INTEGER NOT NULL DEFAULT 0,
            active INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            mobile TEXT NOT NULL,
            address TEXT NOT NULL,
            payment_method TEXT NOT NULL,
            total REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'New',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER,
            product_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE CASCADE
        );
        """)


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("admin_login"))
        return fn(*args, **kwargs)
    return wrapper


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def current_price(product):
    if product["discount_price"] is not None and 0 < product["discount_price"] < product["price"]:
        return float(product["discount_price"])
    return float(product["price"])


def get_cart_details():
    cart = session.get("cart", {})
    if not cart:
        return [], 0.0

    ids = [int(pid) for pid in cart.keys() if str(pid).isdigit()]
    if not ids:
        return [], 0.0

    placeholders = ",".join("?" for _ in ids)
    with get_db() as db:
        rows = db.execute(
            f"SELECT * FROM products WHERE active=1 AND id IN ({placeholders})", ids
        ).fetchall()

    items, total = [], 0.0
    for product in rows:
        qty = max(1, min(99, int(cart.get(str(product["id"]), 1))))
        price = current_price(product)
        line_total = price * qty
        items.append({
            "product": product,
            "quantity": qty,
            "unit_price": price,
            "line_total": line_total
        })
        total += line_total
    return items, round(total, 2)


@app.context_processor
def add_common_values():
    logo_files = list((BASE_DIR / "static").glob("shop-logo.*"))
    logo_name = logo_files[0].name if logo_files else None
    return {"shop_name": os.environ.get("SHOP_NAME", "My Grocery Store"), "shop_logo": logo_name}


@app.route("/")
def home():
    with get_db() as db:
        products = db.execute(
            "SELECT * FROM products WHERE active=1 ORDER BY id DESC"
        ).fetchall()
    return render_template("home.html", products=products)


@app.post("/cart/add/<int:product_id>")
def add_to_cart(product_id):
    with get_db() as db:
        product = db.execute(
            "SELECT id, stock, active FROM products WHERE id=?", (product_id,)
        ).fetchone()
    if not product or not product["active"]:
        abort(404)
    cart = session.get("cart", {})
    current = int(cart.get(str(product_id), 0))
    if current < product["stock"]:
        cart[str(product_id)] = current + 1
        session["cart"] = cart
        flash("Product added to cart.")
    else:
        flash("Sorry, available stock limit reached.")
    return redirect(request.referrer or url_for("home"))


@app.route("/cart", methods=["GET", "POST"])
def cart():
    if request.method == "POST":
        cart_data = session.get("cart", {})
        for pid in list(cart_data.keys()):
            raw = request.form.get(f"qty_{pid}", "0")
            try:
                qty = int(raw)
            except ValueError:
                qty = 0
            if qty <= 0:
                cart_data.pop(pid, None)
            else:
                cart_data[pid] = min(qty, 99)
        session["cart"] = cart_data
        flash("Cart updated.")
        return redirect(url_for("cart"))

    items, total = get_cart_details()
    return render_template("cart.html", items=items, total=total)


@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    items, total = get_cart_details()
    if not items:
        flash("Your cart is empty.")
        return redirect(url_for("home"))

    if request.method == "POST":
        name = request.form.get("customer_name", "").strip()
        mobile = request.form.get("mobile", "").strip()
        address = request.form.get("address", "").strip()
        payment = request.form.get("payment_method", "")

        if not name or not address or not mobile.isdigit() or len(mobile) != 10:
            flash("Enter your name, full address and a valid 10-digit mobile number.")
            return render_template("checkout.html", items=items, total=total)

        if payment not in {"Cash on Delivery", "UPI on delivery"}:
            flash("Please select a valid payment method.")
            return render_template("checkout.html", items=items, total=total)

        with get_db() as db:
            # Re-check stock and prices at order time.
            fresh_items = []
            final_total = 0.0
            for item in items:
                p = db.execute(
                    "SELECT * FROM products WHERE id=? AND active=1",
                    (item["product"]["id"],)
                ).fetchone()
                if not p or p["stock"] < item["quantity"]:
                    flash(f"Not enough stock for {item['product']['name']}. Please update your cart.")
                    return redirect(url_for("cart"))
                price = current_price(p)
                line_total = price * item["quantity"]
                final_total += line_total
                fresh_items.append((p, item["quantity"], price))

            cur = db.execute(
                """INSERT INTO orders
                (customer_name, mobile, address, payment_method, total)
                VALUES (?, ?, ?, ?, ?)""",
                (name, mobile, address, payment, round(final_total, 2))
            )
            order_id = cur.lastrowid
            for p, qty, price in fresh_items:
                db.execute(
                    """INSERT INTO order_items
                    (order_id, product_id, product_name, quantity, unit_price)
                    VALUES (?, ?, ?, ?, ?)""",
                    (order_id, p["id"], p["name"], qty, price)
                )
                db.execute(
                    "UPDATE products SET stock=stock-? WHERE id=?",
                    (qty, p["id"])
                )

        session["cart"] = {}
        return render_template("success.html", order_id=order_id, total=round(final_total, 2))

    return render_template("checkout.html", items=items, total=total)


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        # Demo credentials come from environment variables or defaults above.
        if username == ADMIN_USERNAME and check_password_hash(
            generate_password_hash(ADMIN_PASSWORD), password
        ):
            session["is_admin"] = True
            return redirect(url_for("admin_dashboard"))
        flash("Incorrect username or password.")
    return render_template("admin_login.html")


@app.get("/admin/logout")
def admin_logout():
    session.pop("is_admin", None)
    return redirect(url_for("home"))



@app.post("/admin/logo")
@admin_required
def upload_logo():
    file = request.files.get("logo")
    if not file or not file.filename:
        flash("Choose a logo image first.")
        return redirect(url_for("admin_dashboard"))
    if not allowed_file(file.filename):
        flash("Logo must be PNG, JPG, JPEG or WEBP.")
        return redirect(url_for("admin_dashboard"))
    for old_logo in (BASE_DIR / "static").glob("shop-logo.*"):
        old_logo.unlink(missing_ok=True)
    extension = file.filename.rsplit(".", 1)[1].lower()
    file.save(BASE_DIR / "static" / f"shop-logo.{extension}")
    flash("Shop logo updated.")
    return redirect(url_for("admin_dashboard"))


@app.get("/admin")
@admin_required
def admin_dashboard():
    with get_db() as db:
        products = db.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
        orders = db.execute("SELECT * FROM orders ORDER BY id DESC LIMIT 30").fetchall()
    return render_template("admin.html", products=products, orders=orders)


@app.route("/admin/product/new", methods=["GET", "POST"])
@app.route("/admin/product/<int:product_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_product(product_id=None):
    with get_db() as db:
        product = db.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone() if product_id else None
    if product_id and not product:
        abort(404)

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        category = request.form.get("category", "").strip()
        unit = request.form.get("unit", "1 piece").strip()
        try:
            price = float(request.form.get("price", "0"))
            discount_raw = request.form.get("discount_price", "").strip()
            discount = float(discount_raw) if discount_raw else None
            stock = max(0, int(request.form.get("stock", "0")))
        except ValueError:
            flash("Enter valid numbers for price, discount and stock.")
            return redirect(request.url)

        if not name or price <= 0 or (discount is not None and (discount <= 0 or discount >= price)):
            flash("Enter a product name and valid prices. Discount must be lower than the original price.")
            return redirect(request.url)

        image_name = product["image"] if product else ""
        file = request.files.get("image")
        if file and file.filename:
            if not allowed_file(file.filename):
                flash("Image must be PNG, JPG, JPEG or WEBP.")
                return redirect(request.url)
            safe_name = secure_filename(file.filename)
            image_name = f"{secrets.token_hex(8)}_{safe_name}"
            file.save(UPLOAD_DIR / image_name)

        with get_db() as db:
            values = (name, description, category, unit, price, discount, image_name, stock)
            if product:
                db.execute(
                    """UPDATE products SET name=?, description=?, category=?, unit=?,
                    price=?, discount_price=?, image=?, stock=? WHERE id=?""",
                    values + (product_id,)
                )
            else:
                db.execute(
                    """INSERT INTO products
                    (name, description, category, unit, price, discount_price, image, stock)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", values
                )
        flash("Product saved.")
        return redirect(url_for("admin_dashboard"))

    return render_template("product_form.html", product=product)


@app.post("/admin/product/<int:product_id>/delete")
@admin_required
def delete_product(product_id):
    with get_db() as db:
        db.execute("DELETE FROM products WHERE id=?", (product_id,))
    flash("Product deleted.")
    return redirect(url_for("admin_dashboard"))


@app.post("/admin/order/<int:order_id>/status")
@admin_required
def update_order_status(order_id):
    status = request.form.get("status", "New")
    if status not in {"New", "Accepted", "Preparing", "Out for delivery", "Delivered", "Cancelled"}:
        abort(400)
    with get_db() as db:
        db.execute("UPDATE orders SET status=? WHERE id=?", (status, order_id))
    flash("Order status updated.")
    return redirect(url_for("admin_dashboard"))


@app.get("/admin/order/<int:order_id>")
@admin_required
def order_detail(order_id):
    with get_db() as db:
        order = db.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
        if not order:
            abort(404)
        lines = db.execute("SELECT * FROM order_items WHERE order_id=?", (order_id,)).fetchall()
    return render_template("order.html", order=order, lines=lines)


@app.errorhandler(413)
def too_large(_error):
    return "Image too large. Please upload an image smaller than 5 MB.", 413


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
