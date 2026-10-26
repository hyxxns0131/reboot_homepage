from decimal import Decimal
from flask import render_template, abort, request, url_for, redirect, flash
from wtforms.validators import InputRequired
from core.extensions import db
from core.models import Activity, Submission
from shop.models import ReferralLink, Order
from admin.forms import ReferralLinkForm
from core.activity import record
from auth.decorators import admin_required
from admin import bp
from admin.services import filters, get_orders, reports
from admin.export import csv_response

PRODUCT_FIELDS = 'product_slug product_name order_count units_sold box_units_sold gross_sales_usd discount_usd net_sales_usd via_link_sales_usd'.split()
LINK_FIELDS = 'link_code influencer_name platform clicks order_count conversion_rate units_sold net_sales_usd commission_usd top_product'.split()
ORDER_FIELDS = 'order_id ordered_at status product_slug product_name option_sku option_label flavor quantity unit_price_usd discount_usd line_total_usd link_code influencer_name ship_state is_dummy'.split()


@bp.get('/')
@admin_required
def dashboard():
    f = filters()
    orders = get_orders(f)
    products, links = reports(orders, f)
    total = sum(o.total for o in orders)
    summary = dict(orders=len(orders), units=sum(p['units_sold'] for p in products), total=total, referral_share=sum(o.total for o in orders if o.referral) / total * 100 if total else 0)
    chart = {}
    for order in reversed(orders):
        month = order.ordered_at.strftime('%Y-%m')
        chart[month] = chart.get(month, 0) + order.total
    highest = max(chart.values(), default=1) or 1
    return render_template('admin/dashboard.html', filters=f, products=products, links=links, orders=orders[:15], summary=summary, chart=chart, highest=highest, query=dict(start=f['start'].date().isoformat(), end=f['end'].date().isoformat(), status=f['status'], source=f['source']))


@bp.get('/export/<kind>.csv')
@admin_required
def export(kind):
    if kind not in ('product-sales', 'link-sales', 'orders'):
        abort(404)
    f = filters()
    orders = get_orders(f)
    if kind == 'orders':
        fields = ORDER_FIELDS
        rows = [dict(order_id=o.id, ordered_at=o.ordered_at.isoformat(), status=o.status, product_slug=i.product.slug, product_name=i.product.name, option_sku=i.option.sku, option_label=i.option.label, flavor=i.flavor, quantity=i.quantity, unit_price_usd=i.unit_price, discount_usd=i.line_discount, line_total_usd=i.line_total, link_code=o.referral.code if o.referral else 'DIRECT', influencer_name=o.referral.influencer_name if o.referral else '', ship_state=o.ship_state, is_dummy=o.is_dummy) for o in orders for i in o.items]
    else:
        products, links = reports(orders, f)
        rows, fields = (products, PRODUCT_FIELDS) if kind == 'product-sales' else (links, LINK_FIELDS)
    record('csv_export', {'type': kind, 'rows': len(rows), 'filters': dict(request.args)})
    db.session.commit()
    return csv_response(rows, fields, f'reboot_{kind}_{f["start"]:%Y%m%d}_{f["end"]:%Y%m%d}.csv')


@bp.get('/activity')
@admin_required
def activity():
    page = max(1, request.args.get('page', 1, type=int))
    pagination = db.paginate(db.select(Activity).order_by(Activity.id.desc()), page=page, per_page=40, error_out=False)
    submissions = db.session.scalars(db.select(Submission).order_by(Submission.id.desc()).limit(50)).all()
    return render_template('admin/activity.html', pagination=pagination, submissions=submissions)


def link_form(link=None):
    form = ReferralLinkForm(obj=link)
    # DataRequired rejects 0, but a 0% discount or commission is valid.
    for field in (form.discount_percent, form.commission_percent):
        field.validators = [InputRequired(message='Enter 0 or more.')] + field.validators[1:]
    if link and request.method == 'GET':
        form.discount_percent.data = link.discount_rate * 100
        form.commission_percent.data = link.commission_rate * 100
    return form


def save_link(form, link):
    link.influencer_name = form.influencer_name.data.strip()
    link.platform = form.platform.data
    link.discount_rate = (Decimal(form.discount_percent.data) / 100).quantize(Decimal('0.0001'))
    link.commission_rate = (Decimal(form.commission_percent.data) / 100).quantize(Decimal('0.0001'))
    link.is_active = form.is_active.data


@bp.route('/links', methods=['GET', 'POST'])
@admin_required
def links():
    form = link_form()
    if form.validate_on_submit():
        code = form.code.data.strip().upper()
        if db.session.scalar(db.select(ReferralLink).where(ReferralLink.code == code)):
            form.code.errors.append('This code is already in use.')
        else:
            link = ReferralLink(code=code, clicks=0)
            save_link(form, link)
            db.session.add(link)
            db.session.flush()
            record('referral_link_created', {'code': code})
            db.session.commit()
            flash(f'Creator link /r/{code} is ready.', 'success')
            return redirect(url_for('admin.links'))
    rows = db.session.execute(db.select(ReferralLink, db.func.count(Order.id)).outerjoin(Order, Order.referral_link_id == ReferralLink.id).group_by(ReferralLink.id).order_by(ReferralLink.created_at.desc(), ReferralLink.id.desc())).all()
    return render_template('admin/links.html', form=form, rows=rows), 400 if form.errors else 200


@bp.route('/links/<int:link_id>', methods=['GET', 'POST'])
@admin_required
def edit_link(link_id):
    link = db.get_or_404(ReferralLink, link_id)
    form = link_form(link)
    form.code.data = link.code
    if form.validate_on_submit():
        save_link(form, link)
        record('referral_link_updated', {'code': link.code, 'is_active': link.is_active})
        db.session.commit()
        flash(f'Creator link /r/{link.code} is updated. New rates apply to future orders only.', 'success')
        return redirect(url_for('admin.links'))
    return render_template('admin/link_edit.html', form=form, link=link), 400 if form.errors else 200
