from decimal import Decimal, ROUND_HALF_UP
from flask import request
from core.extensions import db
from shop.models import CartItem, ReferralLink

ZERO = Decimal('0.00')


def money(value):
    return Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def get_cart(user_id):
    return db.session.scalars(db.select(CartItem).where(CartItem.user_id == user_id).order_by(CartItem.id)).all()


def get_referral():
    return db.session.scalar(db.select(ReferralLink).where(ReferralLink.code == request.cookies.get('ref_code', ''), ReferralLink.is_active.is_(True)))


def totals(items, referral=None):
    subtotal = sum((i.option.price * i.quantity for i in items), ZERO)
    discount = sum((money(i.option.price * i.quantity * referral.discount_rate) for i in items), ZERO) if referral else ZERO
    return {'subtotal': subtotal, 'discount': discount, 'total': subtotal - discount}

