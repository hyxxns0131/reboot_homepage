from collections import defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from flask import request, abort
from sqlalchemy.orm import selectinload
from core.extensions import db
from shop.models import Order, OrderItem, ReferralLink, ReferralClick


def filters():
    today = datetime.now(timezone.utc).date()
    try:
        start = datetime.strptime(request.args.get('start', (today - timedelta(days=89)).isoformat()), '%Y-%m-%d')
        end = datetime.strptime(request.args.get('end', today.isoformat()), '%Y-%m-%d')
    except ValueError:
        abort(400, description='Use a valid date in YYYY-MM-DD format.')
    status = request.args.get('status', 'paid')
    if start > end or status not in ('all', 'paid', 'refunded', 'cancelled'):
        abort(400, description='Check the date range and order status.')
    source = request.args.get('source', 'all')
    if source not in ('all', 'sample', 'customer'):
        abort(400)
    return {'start': start, 'end': end, 'status': status, 'source': source}


def get_orders(f):
    query = db.select(Order).where(Order.ordered_at >= f['start'], Order.ordered_at < f['end'] + timedelta(days=1)).options(selectinload(Order.items).selectinload(OrderItem.product), selectinload(Order.items).selectinload(OrderItem.option), selectinload(Order.referral)).order_by(Order.ordered_at.desc())
    if f['status'] != 'all':
        query = query.where(Order.status == f['status'])
    if f['source'] != 'all':
        query = query.where(Order.is_dummy.is_(f['source'] == 'sample'))
    return db.session.scalars(query).all()


def reports(orders, f):
    products = {}
    links = {}
    for link in db.session.scalars(db.select(ReferralLink).order_by(ReferralLink.id)):
        query = db.select(db.func.coalesce(db.func.sum(ReferralClick.count), 0)).where(ReferralClick.referral_link_id == link.id, ReferralClick.created_at >= f['start'], ReferralClick.created_at < f['end'] + timedelta(days=1))
        if f['source'] != 'all':
            query = query.where(ReferralClick.is_dummy.is_(f['source'] == 'sample'))
        links[link.code] = dict(link_code=link.code, influencer_name=link.influencer_name, platform=link.platform, clicks=db.session.scalar(query), order_count=0, conversion_rate=0, units_sold=0, net_sales_usd=Decimal(0), commission_usd=Decimal(0), top_product='', product_units=defaultdict(int))
    links['DIRECT'] = dict(link_code='DIRECT', influencer_name='Direct', platform='—', clicks=0, order_count=0, conversion_rate=0, units_sold=0, net_sales_usd=Decimal(0), commission_usd=Decimal(0), top_product='', product_units=defaultdict(int))
    for order in orders:
        link = links[order.referral.code if order.referral else 'DIRECT']
        link['order_count'] += 1
        link['net_sales_usd'] += order.total
        link['commission_usd'] += order.commission
        seen = set()
        for item in order.items:
            slug = item.product.slug
            if slug not in products:
                products[slug] = dict(product_slug=slug, product_name=item.product.name, order_count=0, units_sold=0, box_units_sold=0, gross_sales_usd=Decimal(0), discount_usd=Decimal(0), net_sales_usd=Decimal(0), via_link_sales_usd=Decimal(0))
            p = products[slug]
            p['order_count'] += int(slug not in seen)
            seen.add(slug)
            p['units_sold'] += item.quantity
            p['box_units_sold'] += item.quantity if item.option.unit_count == 3 else 0
            p['gross_sales_usd'] += item.unit_price * item.quantity
            p['discount_usd'] += item.line_discount
            p['net_sales_usd'] += item.line_total
            p['via_link_sales_usd'] += item.line_total if order.referral else 0
            link['units_sold'] += item.quantity
            link['product_units'][item.product.name] += item.quantity
    for link in links.values():
        link['conversion_rate'] = link['order_count'] / link['clicks'] if link['clicks'] else 0
        link['top_product'] = max(link['product_units'], key=link['product_units'].get) if link['product_units'] else ''
        del link['product_units']
    return sorted(products.values(), key=lambda x: x['net_sales_usd'], reverse=True), sorted(links.values(), key=lambda x: x['net_sales_usd'], reverse=True)

