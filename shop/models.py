from core.extensions import db
from core.models import utcnow


class Product(db.Model):
    __tablename__ = 'shop_product'
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(60), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    options = db.relationship('ProductOption', back_populates='product')


class ProductOption(db.Model):
    __tablename__ = 'shop_product_option'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('shop_product.id'), nullable=False)
    sku = db.Column(db.String(80), unique=True, nullable=False)
    label = db.Column(db.String(80), nullable=False)
    unit_count = db.Column(db.Integer, default=1, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    product = db.relationship('Product', back_populates='options')


class CartItem(db.Model):
    __tablename__ = 'shop_cart_item'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('auth_user.id'), nullable=False, index=True)
    option_id = db.Column(db.Integer, db.ForeignKey('shop_product_option.id'), nullable=False)
    flavor = db.Column(db.String(20), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    option = db.relationship('ProductOption')
    __table_args__ = (db.UniqueConstraint('user_id', 'option_id', 'flavor'), db.CheckConstraint('quantity BETWEEN 1 AND 10'), db.CheckConstraint("flavor IN ('Lime', 'Lemon', 'Cherry')"))


class ReferralLink(db.Model):
    __tablename__ = 'shop_referral_link'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(40), unique=True, nullable=False)
    influencer_name = db.Column(db.String(100), nullable=False)
    platform = db.Column(db.String(40), nullable=False)
    discount_rate = db.Column(db.Numeric(5, 4), nullable=False)
    commission_rate = db.Column(db.Numeric(5, 4), nullable=False)
    clicks = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utcnow)


class ReferralClick(db.Model):
    __tablename__ = 'shop_referral_click'
    id = db.Column(db.Integer, primary_key=True)
    referral_link_id = db.Column(db.Integer, db.ForeignKey('shop_referral_link.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=utcnow, index=True)
    count = db.Column(db.Integer, default=1, nullable=False)
    is_dummy = db.Column(db.Boolean, default=False, nullable=False)


class Order(db.Model):
    __tablename__ = 'shop_order'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('auth_user.id'), index=True)
    referral_link_id = db.Column(db.Integer, db.ForeignKey('shop_referral_link.id'), index=True)
    status = db.Column(db.String(20), default='paid', nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    discount = db.Column(db.Numeric(10, 2), nullable=False)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    commission = db.Column(db.Numeric(10, 2), default=0, nullable=False)
    ship_name = db.Column(db.String(100), nullable=False)
    ship_state = db.Column(db.String(2), nullable=False)
    ship_city = db.Column(db.String(100), nullable=False)
    is_dummy = db.Column(db.Boolean, default=False, nullable=False)
    ordered_at = db.Column(db.DateTime, default=utcnow, index=True)
    checkout_token = db.Column(db.String(64), unique=True)
    items = db.relationship('OrderItem', back_populates='order', cascade='all, delete-orphan')
    referral = db.relationship('ReferralLink')
    __table_args__ = (db.CheckConstraint("status IN ('paid', 'refunded', 'cancelled')"),)


class OrderItem(db.Model):
    __tablename__ = 'shop_order_item'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('shop_order.id'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('shop_product.id'), nullable=False)
    option_id = db.Column(db.Integer, db.ForeignKey('shop_product_option.id'), nullable=False)
    flavor = db.Column(db.String(20), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    line_discount = db.Column(db.Numeric(10, 2), nullable=False)
    line_total = db.Column(db.Numeric(10, 2), nullable=False)
    product = db.relationship('Product')
    option = db.relationship('ProductOption')
    order = db.relationship('Order', back_populates='items')


class CheckoutTicket(db.Model):
    __tablename__ = 'shop_checkout_ticket'
    token = db.Column(db.String(64), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('auth_user.id'), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    consumed_at = db.Column(db.DateTime)

