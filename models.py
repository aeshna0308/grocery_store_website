from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    category = db.Column(
        db.String(80), nullable=False, default="General"
    )
    description = db.Column(db.String(500), default="")
    unit = db.Column(db.String(30), nullable=False, default="piece")
    price = db.Column(db.Float, nullable=False)
    discount_price = db.Column(db.Float, nullable=True)
    stock = db.Column(db.Integer, nullable=False, default=0)
    image = db.Column(db.String(255), default="")
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def selling_price(self):
        if (
            self.discount_price is not None
            and self.discount_price < self.price
        ):
            return self.discount_price
        return self.price


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(120), nullable=False)
    mobile = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(500), nullable=False)
    pincode = db.Column(db.String(12), nullable=False)
    payment_method = db.Column(db.String(20), nullable=False)
    payment_status = db.Column(
        db.String(20), nullable=False, default="Pending"
    )
    status = db.Column(
        db.String(30), nullable=False, default="New"
    )
    subtotal = db.Column(db.Float, nullable=False)
    total = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(
        db.Integer, db.ForeignKey("order.id"), nullable=False
    )
    product_id = db.Column(
        db.Integer, db.ForeignKey("product.id"), nullable=True
    )
    product_name = db.Column(db.String(120), nullable=False)
    unit = db.Column(db.String(30), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    line_total = db.Column(db.Float, nullable=False)

    order = db.relationship(
        "Order", backref=db.backref("items", lazy=True)
    )
