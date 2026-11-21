import re
from urllib.parse import quote

from flask import (
    Blueprint, render_template, request,
    redirect, url_for, session, flash, current_app
)

from models import db, Product, Order, OrderItem
from modules.cart import cart_items

checkout_bp = Blueprint("checkout", __name__)


@checkout_bp.route("/checkout", methods=["GET", "POST"])
def checkout():
    items, subtotal = cart_items()

    if not items:
        flash("Your cart is empty.", "error")
        return redirect(url_for("home"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        mobile = request.form.get("mobile", "").strip()
        address = request.form.get("address", "").strip()
        pincode = request.form.get("pincode", "").strip()
        payment = request.form.get("payment_method", "")

        if (
            not name
            or not re.fullmatch(r"[6-9]\d{9}", mobile)
            or not address
            or not re.fullmatch(r"\d{6}", pincode)
        ):
            flash(
                "Enter a valid name, 10-digit Indian mobile number, "
                "address and 6-digit PIN code.",
                "error"
            )
            return render_template(
                "checkout.html", items=items, total=subtotal
            )

        if payment not in ("UPI", "COD"):
            flash("Please select a valid payment method.", "error")
            return render_template(
                "checkout.html", items=items, total=subtotal
            )

        fresh = []

        for item in items:
            product = Product.query.get(item["product"].id)
            qty = item["quantity"]

            if (
                not product
                or product.stock < qty
                or not product.is_active
            ):
                flash(
                    f"Stock changed for {item['product'].name}. "
                    "Please update your cart.",
                    "error"
                )
                return redirect(url_for("cart.view"))

            fresh.append((product, qty, product.selling_price))

        total = round(
            sum(qty * price for _, qty, price in fresh), 2
        )

        order = Order(
            customer_name=name,
            mobile=mobile,
            address=address,
            pincode=pincode,
            payment_method=payment,
            payment_status="Pending",
            subtotal=total,
            total=total
        )

        db.session.add(order)
        db.session.flush()

        for product, qty, price in fresh:
            product.stock -= qty

            db.session.add(OrderItem(
                order_id=order.id,
                product_id=product.id,
                product_name=product.name,
                unit=product.unit,
                quantity=qty,
                unit_price=price,
                line_total=round(qty * price, 2)
            ))

        db.session.commit()
        session.pop("cart", None)

        upi_id = current_app.config.get("SHOP_UPI_ID", "")
        upi_link = ""

        if payment == "UPI" and upi_id:
            upi_link = (
                f"upi://pay?pa={quote(upi_id)}"
                f"&pn={quote(current_app.config['SHOP_NAME'])}"
                f"&am={total:.2f}&cu=INR"
                f"&tn={quote('Order ' + str(order.id))}"
            )

        return render_template(
            "order_success.html",
            order=order,
            upi_link=upi_link,
            upi_id=upi_id
        )

    return render_template(
        "checkout.html",
        items=items,
        total=subtotal
    )
