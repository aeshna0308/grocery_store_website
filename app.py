import os
from flask import Flask, render_template
from flask_wtf.csrf import CSRFProtect
from models import db
from modules.products import products_bp
from modules.cart import cart_bp
from modules.checkout import checkout_bp
from modules.admin import admin_bp


def create_app():
    app = Flask(__name__, instance_relative_config=True)

    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(os.path.join(app.static_folder, "uploads"), exist_ok=True)

    app.config.update(
        SECRET_KEY=os.environ.get(
            "SECRET_KEY", "dev-only-change-this-secret"
        ),
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            "DATABASE_URL",
            "sqlite:///" + os.path.join(app.instance_path, "grocery.db")
        ).replace("postgres://", "postgresql://", 1),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        MAX_CONTENT_LENGTH=5 * 1024 * 1024,
        SHOP_NAME=os.environ.get("SHOP_NAME", "Fresh Basket"),
        SHOP_UPI_ID=os.environ.get("SHOP_UPI_ID", ""),
        ADMIN_USERNAME=os.environ.get("ADMIN_USERNAME", "admin"),
        ADMIN_PASSWORD=os.environ.get("ADMIN_PASSWORD", "ChangeMe123!"),
    )

    CSRFProtect(app)
    db.init_app(app)

    app.register_blueprint(products_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(checkout_bp)
    app.register_blueprint(admin_bp)

    @app.context_processor
    def inject_shop():
        return {"shop_name": app.config["SHOP_NAME"]}

    @app.route("/")
    def home():
        from models import Product

        products = (
            Product.query
            .filter_by(is_active=True)
            .order_by(Product.name.asc())
            .all()
        )
        return render_template("index.html", products=products)

    @app.errorhandler(404)
    def not_found(error):
        return render_template(
            "message.html",
            title="Page not found",
            message="The page you requested could not be found."
        ), 404

    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
