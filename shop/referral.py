from flask import Blueprint, redirect, url_for, abort, current_app
from core.extensions import db
from core.activity import record
from shop.models import ReferralLink, ReferralClick

bp = Blueprint('referral', __name__)


@bp.get('/r/<code>')
def visit(code):
    link = db.session.scalar(db.select(ReferralLink).where(ReferralLink.code == code.upper(), ReferralLink.is_active.is_(True)))
    if not link:
        abort(404)
    db.session.execute(db.update(ReferralLink).where(ReferralLink.id == link.id).values(clicks=ReferralLink.clicks + 1))
    db.session.add(ReferralClick(referral_link_id=link.id))
    record('referral_visit', {'code': link.code})
    db.session.commit()
    response = redirect(url_for('shop.index'))
    response.set_cookie('ref_code', link.code, max_age=current_app.config['REF_COOKIE_DAYS'] * 86400, secure=current_app.config['SESSION_COOKIE_SECURE'], httponly=True, samesite='Lax')
    return response
