import random
from collections import Counter
from datetime import datetime, timedelta
from decimal import Decimal
from core.extensions import db
from products.services import get_all_products
from shop.models import Product, ProductOption, ReferralLink, ReferralClick, Order, OrderItem
from shop.services import money


def seed_products():
    for data in get_all_products():
        product = db.session.scalar(db.select(Product).where(Product.slug == data['slug']))
        if not product:
            product = Product(slug=data['slug'], name=data['name'])
            db.session.add(product)
            db.session.flush()
        product.name = data['name']
        for entry in data['options']:
            option = db.session.scalar(db.select(ProductOption).where(ProductOption.sku == entry['sku']))
            if not option:
                option = ProductOption(product_id=product.id, sku=entry['sku'])
                db.session.add(option)
            option.label, option.price, option.unit_count = entry['label'], money(entry['price_usd']), entry['unit_count']
    db.session.flush()


def seed_links():
    links = [('NEONNIGHTS', 'Neon Nights', 'TikTok', '.10', '.15'), ('KPARTYLA', 'K-Party LA', 'Instagram', '.10', '.12'), ('MORNINGRESET', 'Morning Reset', 'YouTube', '.15', '.15'), ('SEOULSIPNYC', 'Seoul Sip NYC', 'TikTok', '.10', '.10'), ('BRUNCHCLUB', 'Brunch Club', 'Instagram', '.05', '.10'), ('RESTARTCREW', 'Restart Crew', 'TikTok', '.20', '.20')]
    for code, name, platform, discount, commission in links:
        if not db.session.scalar(db.select(ReferralLink).where(ReferralLink.code == code)):
            db.session.add(ReferralLink(code=code, influencer_name=name, platform=platform, discount_rate=Decimal(discount), commission_rate=Decimal(commission)))
    db.session.flush()


def seed_dummy_orders():
    if db.session.scalar(db.select(db.func.count()).select_from(Order).where(Order.is_dummy.is_(True))):
        return
    rng = random.Random(42)
    products = db.session.scalars(db.select(Product).order_by(Product.id)).all()
    links = db.session.scalars(db.select(ReferralLink).order_by(ReferralLink.id)).all()
    product_counts, link_counts = Counter(), Counter()
    days = [datetime(2026, 1, 1) + timedelta(days=i) for i in range(295)]
    weights = [3 if day.weekday() in (4, 5) else 1 for day in days]
    statuses = ['paid'] * 950 + ['refunded'] * 30 + ['cancelled'] * 20
    rng.shuffle(statuses)
    for n in range(1000):
        link = links[n // 120] if n < 720 else None
        ordered_at = rng.choices(days, weights=weights)[0] + timedelta(hours=rng.choice([19, 20, 21, 22, 23]), minutes=rng.randrange(60))
        selected = [products[n % 4]]
        selected += rng.sample([p for p in products if p not in selected], rng.randrange(3))
        order = Order(user_id=None, referral_link_id=link.id if link else None, status=statuses[n], subtotal=0, discount=0, total=0, commission=0, ship_name='Sample Customer', ship_state=rng.choice(['CA', 'CA', 'NY', 'NY', 'TX', 'WA', 'NJ', 'IL']), ship_city='Sample City', is_dummy=True, ordered_at=ordered_at)
        for product in selected:
            option = rng.choice(product.options)
            quantity = rng.randint(1, 4)
            gross = option.price * quantity
            discount = money(gross * link.discount_rate) if link else money(0)
            order.items.append(OrderItem(product_id=product.id, option_id=option.id, flavor=rng.choice(['Lime', 'Lemon', 'Cherry']), quantity=quantity, unit_price=option.price, line_discount=discount, line_total=gross-discount))
            order.subtotal += gross
            order.discount += discount
            product_counts[product.slug] += 1
        order.total = order.subtotal - order.discount
        order.commission = money(order.total * link.commission_rate) if link else money(0)
        db.session.add(order)
        if link:
            link_counts[link.code] += 1
            clicks = rng.randint(8, 20)
            link.clicks += clicks
            db.session.add(ReferralClick(referral_link_id=link.id, created_at=ordered_at - timedelta(hours=1), count=clicks, is_dummy=True))
    assert all(product_counts[p.slug] >= 100 for p in products)
    assert all(link_counts[link.code] >= 100 for link in links)
    db.session.flush()

