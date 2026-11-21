import os
import uuid
from functools import wraps

from flask import (
    Blueprint, current_app, request, render_template,
    redirect, url_for, session, flash
)
from werkzeug.security import check_password_hash
from models import db, Product, Order

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

ALLOWED = {"png", "jpg", "jpeg", "webp"}


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(
                url_for("admin.login", next=request.path)
            )
        return fn(*args, **kwargs)
    return wrapper


def save_image(file):
    if not file or not file.filename:
        return ""

    ext = (
        file.filename.rsplit(".", 1)[-1].lower()
        if "." in file.filename else ""
    )

    if ext not in ALLOWED:
        raise ValueError(
            "Use a PNG, JPG, JPEG or WEBP image."
        )

    filename = f"{uuid.uuid4().hex}.{ext}"

    file.save(
        os.path.join(
            current_app.static_folder,
            "uploads",
            filename
        )
    )

    return filename


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        expected_user = current_app.config["ADMIN_USERNAME"]
        expected_password = current_app.config["ADMIN_PASSWORD"]

        if expected_password.startswith(("pbkdf2:", "scrypt:")):
            valid_password = check_password_hash(
                expected_password, password
            )
        else:
            valid_password = password == expected_password

        if username == expected_user and valid_password:
            session.clear()
            session["is_admin"] = True

            flash(
                "Welcome to the admin dashboard.",
                "success"
            )

            return redirect(url_for("admin.dashboard"))

        flash("Invalid username or password.", "error")

    return render_template("admin/login.html")


@admin_bp.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


@admin_bp.get("/")
@admin_required
def dashboard():
    products = Product.query.order_by(
        Product.created_at.desc()
    ).all()

    orders = Order.query.order_by(
        Order.created_at.desc()
    ).limit(10).all()

    return render_template(
        "admin/dashboard.html",
        products=products,
        orders=orders
    )


@admin_bp.route("/products/new", methods=["GET", "POST"])
@admin_required
def new_product():
    return product_form(None)


@admin_bp.route(
    "/products/<int:product_id>/edit",
    methods=["GET", "POST"]
)
@admin_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    return product_form(product)


def product_form(product):
    if request.method == "POST":
        try:
            name = request.form.get("name", "").strip()
            category = request.form.get("category", "").strip()
            unit = request.form.get("unit", "piece").strip()

            price = float(request.form.get("price", "0"))

            discount_raw = request.form.get(
                "discount_price", ""
            ).strip()

            discount = (
                float(discount_raw)
                if discount_raw else None
            )

            stock = int(request.form.get("stock", "0"))

            if (
                not name
                or not category
                or price <= 0
                or stock < 0
                or (
                    discount is not None
                    and (discount <= 0 or discount >= price)
                )
            ):
                raise ValueError(
                    "Check product name, category, price, "
                    "discount and stock values."
                )

            if product is None:
                product = Product(
                    name=name,
                    category=category,
                    unit=unit,
                    price=price,
                    stock=stock
                )
                db.session.add(product)

            product.name = name
            product.category = category
            product.unit = unit
            product.description = request.form.get(
                "description", ""
            ).strip()
            product.price = price
            product.discount_price = discount
            product.stock = stock
            product.is_active = (
                request.form.get("is_active") == "on"
            )

            image = request.files.get("image")

            if image and image.filename:
                product.image = save_image(image)

            db.session.commit()

            flash("Product saved successfully.", "success")

            return redirect(url_for("admin.dashboard"))

        except (ValueError, TypeError) as exc:
            flash(str(exc), "error")

    return render_template(
        "admin/product_form.html",
        product=product
    )


@admin_bp.post("/products/<int:product_id>/delete")
@admin_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)

    # Hide instead of permanently deleting.
    product.is_active = False

    db.session.commit()

    flash("Product hidden from the shop.", "success")

    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/orders")
@admin_required
def orders():
    all_orders = Order.query.order_by(
        Order.created_at.desc()
    ).all()

    return render_template(
        "admin/orders.html",
        orders=all_orders
    )


@admin_bp.post("/orders/<int:order_id>/status")
@admin_required
def update_order(order_id):
    order = Order.query.get_or_404(order_id)

    status = request.form.get("status")

    allowed = {
        "New",
        "Accepted",
        "Packed",
        "Out for delivery",
        "Delivered",
        "Cancelled"
    }

    if status in allowed:
        order.status = status

        if (
            status == "Delivered"
            and order.payment_method == "COD"
        ):
            order.payment_status = "Paid"

        db.session.commit()

        flash("Order status updated.", "success")

    return redirect(url_for("admin.orders"))


@admin_bp.post("/orders/<int:order_id>/payment")
@admin_required
def update_payment(order_id):
    order = Order.query.get_or_404(order_id)

    payment_status = request.form.get("payment_status")

    if payment_status in {"Pending", "Paid", "Failed"}:
        order.payment_status = payment_status
        db.session.commit()

        flash(
            "Payment status updated. Verify UPI receipt "
            "before marking paid.",
            "success"
        )

    return redirect(url_for("admin.orders"))
