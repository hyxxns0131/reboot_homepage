from pathlib import Path
import sqlite3
from flask import Flask, render_template, request, send_from_directory, g
from flask_login import current_user
from flask_wtf.csrf import CSRFError
from sqlalchemy import event
from sqlalchemy.engine import Engine
from config import Config, ROOT
from core.extensions import db, login_manager, csrf


@event.listens_for(Engine, 'connect')
def sqlite_foreign_keys(connection, _):
    if isinstance(connection, sqlite3.Connection):
        connection.execute('PRAGMA foreign_keys=ON')
        connection.execute('PRAGMA busy_timeout=15000')


def create_app(test_config=None):
    app = Flask(__name__, template_folder='core/templates', static_folder='core/static', instance_relative_config=True)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)
    if not app.config['SECRET_KEY']:
        raise RuntimeError('SECRET_KEY is missing. Run scripts/setup_local.py or configure the environment.')
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Sign in to keep your bag and orders together.'
    csrf.init_app(app)
    import auth.models
    import shop.models
    import core.models
    from main import bp as main_bp
    from auth import bp as auth_bp
    from products import bp as products_bp
    from shop import bp as shop_bp
    from shop.referral import bp as referral_bp
    from admin import bp as admin_bp
    for blueprint in (main_bp, auth_bp, products_bp, shop_bp, referral_bp, admin_bp):
        app.register_blueprint(blueprint)
    from core.cli import register_cli
    register_cli(app)
    from products.services import get_product, get_all_products
    from shop.models import CartItem
    app.jinja_env.globals.update(get_product=get_product, all_products=get_all_products)
    app.jinja_env.filters['usd'] = lambda value: f'${value:,.2f}'

    @app.before_request
    def load_language():
        g.locale = request.cookies.get('reboot_language', 'en')
        if g.locale not in ('en', 'ko'):
            g.locale = 'en'
        if request.endpoint not in ('static', 'media', 'health') and current_user.is_authenticated:
            from core.models import Preference
            pref = db.session.scalar(db.select(Preference).where(Preference.user_id == current_user.id))
            if pref:
                g.locale = pref.language

    @app.context_processor
    def shared_context():
        count = db.session.scalar(db.select(db.func.coalesce(db.func.sum(CartItem.quantity), 0)).where(CartItem.user_id == current_user.id)) if current_user.is_authenticated and current_user.role == 'customer' else 0
        return {'cart_count': count, 'locale': getattr(g, 'locale', 'en')}

    @app.get('/media/<path:filename>')
    def media(filename):
        return send_from_directory(ROOT / 'images', filename, max_age=86400)

    @app.get('/healthz')
    def health():
        db.session.execute(db.text('SELECT 1'))
        return {'status': 'ok'}

    @app.after_request
    def finish_request(response):
        if response.mimetype == 'text/html' and getattr(g, 'locale', 'en') == 'ko':
            from core.i18n import korean_html
            response.set_data(korean_html(response.get_data(as_text=True)))
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
        response.headers['Content-Security-Policy'] = "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self'; font-src 'self'; connect-src 'self'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'"
        if app.config['SESSION_COOKIE_SECURE']:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        if request.endpoint not in ('static', 'media'):
            response.headers['Cache-Control'] = 'no-store'
        if request.method == 'GET' and response.status_code == 200 and response.mimetype == 'text/html' and current_user.is_authenticated:
            from core.activity import record
            record('page_view')
            db.session.commit()
        return response

    @app.errorhandler(CSRFError)
    def csrf_error(error):
        return render_template('core/error.html', code=400, message='Your form session expired. Refresh the page and try again.'), 400

    def handle_error(error):
        db.session.rollback()
        code = getattr(error, 'code', 500)
        messages = {400: 'Something in that request needs another look.', 403: 'This area is for a different account role.', 404: 'Looks like this page took the night off.', 405: 'That action needs a form submission.', 413: 'That message is a little too large.', 500: 'We hit a little pause. Please try again.'}
        return render_template('core/error.html', code=code, message=messages.get(code, 'Something went wrong.')), code
    for code in (400, 403, 404, 405, 413, 500):
        app.register_error_handler(code, handle_error)
    return app

