from flask import render_template, request, redirect, url_for, flash, abort, current_app, Response
from flask_login import current_user
from main import bp
from main.forms import ContactForm
from main.content import ARTICLES
from products.services import get_all_products, get_product
from core.extensions import db
from core.models import Submission, QuizResult
from core.activity import record
from flask_login import login_required


@bp.get('/')
def home():
    return render_template('main/index.html', products=get_all_products(), articles=ARTICLES)


@bp.get('/about/story')
def story():
    return render_template('main/story.html')


@bp.get('/where-to-buy/')
def where_to_buy():
    return render_template('main/where.html')


@bp.get('/feed/')
def feed():
    return render_template('main/feed.html', articles=ARTICLES)


@bp.get('/feed/<slug>')
def article(slug):
    article = next((a for a in ARTICLES if a['slug'] == slug), None)
    if not article:
        abort(404)
    return render_template('main/article.html', article=article)


def submission(kind):
    form = ContactForm()
    if form.validate_on_submit():
        row = Submission(user_id=current_user.id if current_user.is_authenticated else None, kind=kind, name=form.name.data.strip(), email=form.email.data.strip().lower(), subject=form.subject.data.strip(), message=form.message.data.strip())
        db.session.add(row)
        db.session.flush()
        record(f'{kind}_submitted', {'submission_id': row.id})
        db.session.commit()
        flash('Your message is saved. Thank you for reaching out to Reboot.', 'success')
        return redirect(url_for('main.creators' if kind == 'creator' else 'main.contact', sent='1'))
    return render_template('main/contact.html', form=form, creator=kind == 'creator', sent=request.args.get('sent') == '1')


@bp.route('/contact/', methods=['GET', 'POST'])
def contact():
    return submission('contact')


@bp.route('/creators/', methods=['GET', 'POST'])
def creators():
    return submission('creator')


@bp.route('/vibe-test/', methods=['GET', 'POST'])
def vibe():
    if request.method == 'POST':
        answers = [request.form.get(f'q{i}') for i in range(3)]
        if answers[0] not in ('out', 'in') or answers[1] not in ('drink', 'jelly') or answers[2] not in ('Lime', 'Lemon', 'Cherry'):
            flash('Answer all three questions to find your Reboot.', 'error')
            return render_template('main/vibe.html'), 400
        slug = f'{answers[1]}-{"original" if answers[0] == "out" else "balance"}'
        result = QuizResult(user_id=current_user.id if current_user.is_authenticated else None, answers=answers, product_slug=slug)
        db.session.add(result)
        record('vibe_completed', {'product': slug, 'flavor': answers[2]})
        db.session.commit()
        return render_template('main/vibe-result.html', product=get_product(slug), flavor=answers[2])
    return render_template('main/vibe.html')


@bp.get('/game/')
def game():
    return render_template('main/game.html')


@bp.get('/robots.txt')
def robots():
    lines = ['User-agent: *', 'Disallow: /admin/', 'Disallow: /auth/', 'Disallow: /shop/cart', 'Disallow: /shop/checkout', 'Disallow: /shop/orders', 'Disallow: /r/', f"Sitemap: {url_for('main.sitemap', _external=True)}"]
    return Response('\n'.join(lines) + '\n', mimetype='text/plain')


@bp.get('/sitemap.xml')
def sitemap():
    pages = [url_for(endpoint, _external=True) for endpoint in ('main.home', 'main.story', 'products.index', 'shop.index', 'main.feed', 'main.where_to_buy', 'main.vibe', 'main.game', 'main.creators', 'main.contact')]
    pages += [url_for('products.detail', slug=p['slug'], _external=True) for p in get_all_products()]
    pages += [url_for('main.article', slug=a['slug'], _external=True) for a in ARTICLES]
    pages += [url_for('main.legal', page=page, _external=True) for page in ('privacy', 'terms', 'cookies')]
    return render_template('main/sitemap.xml', pages=pages), 200, {'Content-Type': 'application/xml; charset=utf-8'}


@bp.get('/legal/')
@bp.get('/legal/<page>')
def legal(page='privacy'):
    if page not in ('privacy', 'terms', 'cookies'):
        abort(404)
    return render_template('main/legal.html', page=page)


@bp.post('/activity')
@login_required
def activity():
    data = request.get_json(silent=True) or {}
    event = data.get('event')
    value = data.get('value')
    if event not in ('flavor_selected', 'collection_filtered', 'motion_preference', 'quiz_step', 'game_score') or not isinstance(value, str) or len(value) > 80:
        abort(400)
    record(event, {'value': value})
    db.session.commit()
    return '', 204


@bp.post('/language')
def language():
    from core.models import Preference
    from auth.routes import safe_next
    locale = request.form.get('language')
    if locale not in ('en', 'ko'):
        abort(400)
    if current_user.is_authenticated:
        pref = db.session.scalar(db.select(Preference).where(Preference.user_id == current_user.id))
        if not pref:
            pref = Preference(user_id=current_user.id, language=locale)
            db.session.add(pref)
        pref.language = locale
        record('language_changed', {'language': locale})
        db.session.commit()
    response = redirect(safe_next(request.form.get('next')) or url_for('main.home'))
    response.set_cookie('reboot_language', locale, max_age=365 * 86400, httponly=True, secure=current_app.config['SESSION_COOKIE_SECURE'], samesite='Lax')
    return response

