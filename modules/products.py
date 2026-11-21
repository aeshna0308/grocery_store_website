from flask import Blueprint, request, render_template
from models import Product

products_bp = Blueprint("products", __name__)


@products_bp.get("/products")
def listing():
    q = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()

    query = Product.query.filter_by(is_active=True)

    if q:
        query = query.filter(Product.name.ilike(f"%{q}%"))

    if category:
        query = query.filter_by(category=category)

    products = query.order_by(Product.name.asc()).all()

    categories = [
        row[0]
        for row in Product.query
        .with_entities(Product.category)
        .filter_by(is_active=True)
        .distinct()
        .all()
    ]

    return render_template(
        "products.html",
        products=products,
        categories=categories,
        q=q,
        selected_category=category
    )
