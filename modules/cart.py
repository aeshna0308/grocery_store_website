from flask import (
    Blueprint, session, redirect, url_for,
    request, flash, render_template
)
from models import Product

cart_bp = Blueprint("cart", __name__, url_prefix="/cart")


def cart_items():
    cart = session.get("cart", {})
    items = []
    total = 0

    for product_id, quantity in cart.items():
        product = Product.query.get(int(product_id))

        if not product or not product.is_active:
            continue

        quantity = max(1, min(int(quantity), product.stock))

        line_total = product.selling_price * quantity

        items.append({
            "product": product,
            "quantity": quantity,
            "line_total": line_total
        })

        total += line_total

    return items, round(total, 2)


@cart_bp.post("/add/<int:product_id>")
def add(product_id):
    product = Product.query.get_or_404(product_id)

    if not product.is_active or product.stock < 1:
        flash("This product is currently unavailable.", "error")
        return redirect(request.referrer or url_for("home"))

    cart = session.get("cart", {})
    current = int(cart.get(str(product_id), 0))

    if current < product.stock:
        cart[str(product_id)] = current + 1
        session["cart"] = cart
        flash(f"{product.name} added to your cart.", "success")
    else:
        flash("You have reached the available stock quantity.", "error")

    return redirect(request.referrer or url_for("home"))


@cart_bp.get("/")
def view():
    items, total = cart_items()

    return render_template(
        "cart.html",
        items=items,
        total=total
    )


@cart_bp.post("/update")
def update():
    cart = session.get("cart", {})

    for product_id in list(cart.keys()):
        try:
            qty = int(
                request.form.get(f"qty_{product_id}", "0")
            )
        except ValueError:
            qty = 0

        product = Product.query.get(int(product_id))

        if qty <= 0 or not product:
            cart.pop(product_id, None)
        else:
            cart[product_id] = min(qty, product.stock)

    session["cart"] = cart

    flash("Your cart has been updated.", "success")
    return redirect(url_for("cart.view"))


@cart_bp.post("/remove/<int:product_id>")
def remove(product_id):
    cart = session.get("cart", {})
    cart.pop(str(product_id), None)

    session["cart"] = cart

    flash("Item removed from cart.", "success")
    return redirect(url_for("cart.view"))
