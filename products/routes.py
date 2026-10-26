from flask import render_template, abort
from products import bp
from products.services import get_all_products, get_product
from shop.models import Product, ProductOption
from core.extensions import db


@bp.get('/')
def index():
    return render_template('products/index.html', products=get_all_products())


@bp.get('/<slug>')
def detail(slug):
    product = get_product(slug)
    if not product:
        abort(404)
    options = db.session.scalars(db.select(ProductOption).join(Product).where(Product.slug == slug, ProductOption.is_active.is_(True)).order_by(ProductOption.price)).all()
    return render_template('products/detail.html', product=product, options=options)

