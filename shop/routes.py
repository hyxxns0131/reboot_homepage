import secrets
from datetime import timedelta
from flask import render_template, redirect, url_for, request, abort, flash
from flask_login import current_user
from sqlalchemy.exc import IntegrityError
from shop import bp
from shop.models import ProductOption, CartItem, Order, OrderItem, CheckoutTicket
from shop.services import get_cart, get_referral, totals, money
from shop.forms import CheckoutForm
from products.services import get_all_products, get_product
from core.extensions import db
from core.models import utcnow
from core.activity import record
from auth.decorators import customer_required


@bp.get('/')
def index():
    return render_template('products/index.html', products=get_all_products(), shopping=True)


@bp.route('/cart', methods=['GET'])
@customer_required
def cart():
    items = get_cart(current_user.id)
    referral = get_referral()
    return render_template('shop/cart.html', items=items, totals=totals(items, referral), referral=referral)


@bp.post('/cart/add')
@customer_required
def add():
    option = db.session.scalar(db.select(ProductOption).where(ProductOption.sku == request.form.get('sku'), ProductOption.is_active.is_(True)))
    flavor = request.form.get('flavor')
    quantity = request.form.get('quantity', type=int)
    if not option or not option.product.is_active or flavor not in get_product(option.product.slug)['flavors'] or quantity is None or not 1 <= quantity <= 10:
        abort(400)
    item = db.session.scalar(db.select(CartItem).where(CartItem.user_id == current_user.id, CartItem.option_id == option.id, CartItem.flavor == flavor))
    if item:
        if item.quantity + quantity > 10:
            flash('You can add up to 10 of each flavor and pack.', 'error')
            return redirect(url_for('shop.cart'))
        item.quantity += quantity
    else:
        db.session.add(CartItem(user_id=current_user.id, option_id=option.id, flavor=flavor, quantity=quantity))
    record('cart_add', {'sku': option.sku, 'flavor': flavor, 'quantity': quantity})
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash('Your bag changed in another window. Please try again.', 'error')
        return redirect(url_for('shop.cart'))
    flash('Good choice. Added to your bag.', 'success')
    return redirect(url_for('shop.cart'))


@bp.post('/cart/<int:item_id>')
@customer_required
def update(item_id):
    item = db.session.scalar(db.select(CartItem).where(CartItem.id == item_id, CartItem.user_id == current_user.id))
    if not item:
        abort(404)
    quantity = 0 if request.form.get('action') == 'remove' else request.form.get('quantity', type=int)
    if quantity is None or not 0 <= quantity <= 10:
        abort(400)
    if quantity == 0:
        db.session.delete(item)
    else:
        item.quantity = quantity
    record('cart_update', {'item_id': item_id, 'quantity': quantity})
    db.session.commit()
    return redirect(url_for('shop.cart'))


@bp.route('/checkout', methods=['GET', 'POST'])
@customer_required
def checkout():
    form = CheckoutForm()
    if request.method == 'POST' and form.validate_on_submit():
        prior = db.session.scalar(db.select(Order).where(Order.checkout_token == form.checkout_token.data, Order.user_id == current_user.id))
        if prior:
            return redirect(url_for('shop.order_detail', order_id=prior.id))
        claimed = db.session.execute(db.update(CheckoutTicket).where(CheckoutTicket.token == form.checkout_token.data, CheckoutTicket.user_id == current_user.id, CheckoutTicket.consumed_at.is_(None), CheckoutTicket.expires_at > utcnow()).values(consumed_at=utcnow()))
        if claimed.rowcount != 1:
            db.session.rollback()
            flash('This checkout expired or was already submitted. Please review your bag.', 'error')
            return redirect(url_for('shop.cart'))
        # Serialize checkouts for one customer on PostgreSQL; SQLite serializes the ticket write above.
        from auth.models import User
        db.session.execute(db.select(User.id).where(User.id == current_user.id).with_for_update())
        items = get_cart(current_user.id)
        if not items or any(not i.option.is_active or not i.option.product.is_active for i in items):
            db.session.rollback()
            flash('Please review the available items in your bag.', 'error')
            return redirect(url_for('shop.cart'))
        referral = get_referral()
        amounts = totals(items, referral)
        order = Order(user_id=current_user.id, referral_link_id=referral.id if referral else None, status='paid', ship_name=form.name.data.strip(), ship_city=form.city.data.strip(), ship_state=form.state.data, checkout_token=form.checkout_token.data, commission=money(amounts['total'] * referral.commission_rate) if referral else 0, **amounts)
        db.session.add(order)
        db.session.flush()
        for item in items:
            gross = item.option.price * item.quantity
            discount = money(gross * referral.discount_rate) if referral else money(0)
            order.items.append(OrderItem(product_id=item.option.product_id, option_id=item.option_id, flavor=item.flavor, quantity=item.quantity, unit_price=item.option.price, line_discount=discount, line_total=gross - discount))
            db.session.delete(item)
        record('order_placed', {'order_id': order.id, 'total': str(order.total), 'mock': True})
        db.session.commit()
        return redirect(url_for('shop.order_detail', order_id=order.id))
    items = get_cart(current_user.id)
    if not items:
        flash('Your bag is waiting for a little Reboot.', 'info')
        return redirect(url_for('shop.cart'))
    if request.method == 'GET':
        form.name.data = current_user.name
        form.checkout_token.data = secrets.token_hex(24)
        db.session.add(CheckoutTicket(token=form.checkout_token.data, user_id=current_user.id, expires_at=utcnow() + timedelta(hours=3)))
        db.session.commit()
    referral = get_referral()
    return render_template('shop/checkout.html', form=form, items=items, totals=totals(items, referral), referral=referral)


@bp.get('/orders')
@customer_required
def orders():
    orders = db.session.scalars(db.select(Order).where(Order.user_id == current_user.id).order_by(Order.ordered_at.desc())).all()
    return render_template('shop/orders.html', orders=orders)


@bp.get('/orders/<int:order_id>')
@customer_required
def order_detail(order_id):
    order = db.session.scalar(db.select(Order).where(Order.id == order_id, Order.user_id == current_user.id))
    if not order:
        abort(404)
    return render_template('shop/order.html', order=order)

