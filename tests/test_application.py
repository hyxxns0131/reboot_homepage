import csv
import io
from datetime import datetime
from decimal import Decimal
import pytest
from core.extensions import db
from core.models import Activity, Submission, QuizResult
from auth.models import User, LoginSession
from shop.models import CartItem, Order, Product, ReferralLink, OrderItem
from shop.seed import seed_dummy_orders
from admin.export import safe_cell
from conftest import csrf, login, logout, add_item, checkout, TEST_PASSWORD


@pytest.mark.parametrize('path', ['/', '/about/story', '/products/', '/products/drink-original', '/products/drink-balance', '/products/jelly-original', '/products/jelly-balance', '/shop/', '/feed/', '/feed/meet-your-new-ritual', '/where-to-buy/', '/vibe-test/', '/creators/', '/contact/', '/legal/', '/legal/terms', '/legal/cookies', '/auth/login', '/auth/register', '/healthz', '/game/', '/robots.txt', '/sitemap.xml'])
def test_public_routes(client, path):
    assert client.get(path).status_code == 200


def test_registration_role_csrf_duplicate_and_age(client, app):
    data = dict(name='New Customer', email='new@example.com', password=TEST_PASSWORD, confirm=TEST_PASSWORD, age='y', role='admin')
    assert client.post('/auth/register', data=data).status_code == 400
    data['csrf_token'] = csrf(client, '/auth/register')
    no_age = {**data, 'age': ''}
    assert b'Please confirm' in client.post('/auth/register', data=no_age).data
    assert client.post('/auth/register', data=data).status_code == 302
    with app.app_context():
        user = db.session.scalar(db.select(User).where(User.email == 'new@example.com'))
        assert user.role == 'customer' and user.age_confirmed_at
        assert user.password_hash != TEST_PASSWORD and user.check_password(TEST_PASSWORD)
    assert client.get('/admin/').status_code == 403
    logout(client)
    data['csrf_token'] = csrf(client, '/auth/register')
    assert client.post('/auth/register', data=data).status_code == 400


def test_auth_roles_and_revoked_session(client, app):
    assert client.get('/shop/cart').status_code == 302
    assert client.get('/admin/export/orders.csv').status_code == 302
    login(client, remember=True)
    remember = client.get_cookie('remember_token').value
    assert client.get('/admin/').status_code == 403
    assert client.get('/admin/activity').status_code == 403
    assert client.get('/admin/export/orders.csv').status_code == 403
    assert client.get('/auth/logout').status_code == 405
    assert client.post('/auth/logout').status_code == 400
    assert logout(client).status_code == 302
    client.set_cookie('remember_token', remember)
    assert client.get('/shop/cart').status_code == 302
    login(client, 'admin@example.com')
    assert client.get('/admin/').status_code == 200
    assert client.get('/admin/activity').status_code == 200
    assert client.get('/shop/cart').status_code == 403
    assert client.get('/shop/checkout').status_code == 403


@pytest.mark.parametrize('next_path', ['//evil.example', 'https://evil.example', '/\\evil.example', '/%5Cevil.example', '/%0aevil.example'])
def test_no_open_redirect(client, next_path):
    from urllib.parse import urlencode
    response = login(client, next_path='?' + urlencode({'next': next_path}))
    assert response.location == '/'


def test_login_rate_limit(client):
    token = csrf(client)
    for _ in range(10):
        response = client.post('/auth/login', data={'csrf_token': token, 'email': 'customer@example.com', 'password': 'wrong'})
        assert response.status_code == 200
    assert client.post('/auth/login', data={'csrf_token': token, 'email': 'customer@example.com', 'password': TEST_PASSWORD}).status_code == 429


def test_cart_persists_and_checkout_is_server_priced_and_idempotent(client, app):
    login(client)
    assert add_item(client).status_code == 302
    assert add_item(client, quantity=11).status_code == 400
    assert add_item(client, flavor='Invalid').status_code == 400
    logout(client)
    login(client)
    assert b'2' in client.get('/shop/cart').data
    client.get('/r/NEONNIGHTS')
    data = checkout(client)
    response = client.post('/shop/checkout', data={**data, 'total': '0.01'})
    assert response.status_code == 302
    assert client.post('/shop/checkout', data=data).location == response.location
    assert client.get(response.location).status_code == 200
    assert client.get('/shop/orders').status_code == 200
    with app.app_context():
        orders = db.session.scalars(db.select(Order)).all()
        assert len(orders) == 1
        order = orders[0]
        assert order.subtotal == Decimal('38.00')
        assert order.discount == Decimal('3.80')
        assert order.total == Decimal('34.20')
        assert order.referral.code == 'NEONNIGHTS'
        assert order.items[0].flavor == 'Lime' and order.items[0].quantity == 2
        assert db.session.scalar(db.select(db.func.count()).select_from(CartItem)) == 0
        assert db.session.scalar(db.select(Activity).where(Activity.event == 'order_placed')) is not None


def test_cart_remove_and_ownership(client, app):
    login(client)
    add_item(client)
    with app.app_context():
        item_id = db.session.scalar(db.select(CartItem.id))
    other = app.test_client()
    data = dict(csrf_token=csrf(other, '/auth/register'), name='Other Person', email='other@example.com', password=TEST_PASSWORD, confirm=TEST_PASSWORD, age='y')
    other.post('/auth/register', data=data)
    assert other.post(f'/shop/cart/{item_id}', data={'csrf_token': csrf(other, '/'), 'quantity': 0}).status_code == 404
    result = client.post('/shop/checkout', data=checkout(client))
    assert other.get(result.location).status_code == 404
    add_item(client)
    with app.app_context():
        new_id = db.session.scalar(db.select(CartItem.id))
    assert client.post(f'/shop/cart/{new_id}', data={'csrf_token': csrf(client, '/'), 'quantity': 2, 'action': 'remove'}).status_code == 302
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count()).select_from(CartItem)) == 0


def test_contact_creator_quiz_and_activity_saved(client, app):
    login(client)
    for path in ['/contact/', '/creators/']:
        data = dict(csrf_token=csrf(client, path), name='Test Person', email='person@example.com', subject='<script>alert(1)</script>', message='A message for the Reboot team.', consent='y')
        assert client.post(path, data=data).status_code == 302
    assert client.post('/vibe-test/', data={'csrf_token': csrf(client, '/vibe-test/'), 'q0': 'in', 'q1': 'jelly', 'q2': 'Lemon'}).status_code == 200
    assert client.post('/activity', json={'event': 'flavor_selected', 'value': 'Lemon'}, headers={'X-CSRFToken': csrf(client, '/')}).status_code == 204
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count()).select_from(Submission)) == 2
        result = db.session.scalar(db.select(QuizResult))
        assert result.product_slug == 'jelly-balance' and result.user_id
        assert db.session.scalar(db.select(Activity).where(Activity.event == 'flavor_selected')) is not None
    logout(client)
    login(client, 'admin@example.com')
    assert b'&lt;script&gt;' in client.get('/admin/activity').data


def test_seed_counts_idempotence_and_csv_filters(client, app):
    with app.app_context():
        seed_dummy_orders()
        db.session.commit()
        seed_dummy_orders()
        assert db.session.scalar(db.select(db.func.count()).select_from(Order)) == 1000
        for product in db.session.scalars(db.select(Product)):
            assert db.session.scalar(db.select(db.func.count(db.distinct(OrderItem.order_id))).where(OrderItem.product_id == product.id)) >= 100
        for link in db.session.scalars(db.select(ReferralLink)):
            assert db.session.scalar(db.select(db.func.count()).select_from(Order).where(Order.referral_link_id == link.id)) == 120
        expected = sum(db.session.scalars(db.select(Order.total).where(Order.status == 'paid')))
    login(client, 'admin@example.com')
    args = '?start=2026-01-01&end=2026-10-22&status=paid&source=sample'
    assert client.get('/admin/' + args).status_code == 200
    totals = []
    for kind in ['product-sales', 'link-sales', 'orders']:
        response = client.get(f'/admin/export/{kind}.csv' + args)
        assert response.status_code == 200 and response.data.startswith(b'\xef\xbb\xbf')
        assert 'attachment' in response.headers['Content-Disposition']
        rows = list(csv.DictReader(io.StringIO(response.data.decode('utf-8-sig'))))
        column = 'line_total_usd' if kind == 'orders' else 'net_sales_usd'
        totals.append(sum(Decimal(row[column]) for row in rows))
        if kind == 'orders':
            assert all(row['status'] == 'paid' and row['is_dummy'] == 'True' for row in rows)
    assert totals == [expected] * 3
    assert client.get('/admin/?start=invalid').status_code == 400
    assert client.get('/admin/?start=2026-11-01&end=2026-01-01').status_code == 400
    empty = client.get('/admin/export/orders.csv?start=2026-01-01&end=2026-10-22&source=customer')
    assert len(list(csv.reader(io.StringIO(empty.data.decode('utf-8-sig'))))) == 1


@pytest.mark.parametrize('cell', ['=SUM(1,2)', '+1+1', '-1+1', '@SUM(1)', '\t=1', '\r=1', '  =1'])
def test_csv_formula_injection(cell):
    assert safe_cell(cell).startswith("'")


def test_referral_last_click_and_guest_storage(client, app):
    assert client.get('/r/MISSING').status_code == 404
    client.get('/r/NEONNIGHTS')
    client.get('/r/BRUNCHCLUB')
    assert client.get_cookie('ref_code').value == 'BRUNCHCLUB'
    login(client)
    add_item(client, sku='drink-original-single', quantity=1)
    client.post('/shop/checkout', data=checkout(client))
    with app.app_context():
        assert db.session.scalar(db.select(Order)).total == Decimal('6.65')


def test_language_switch_csrf_and_account_preference(client, app):
    assert client.post('/language', data={'language': 'ko'}).status_code == 400
    token = csrf(client, '/')
    assert client.post('/language', data={'language': 'ko', 'csrf_token': token, 'next': 'https://evil.example'}).location == '/'
    korean = client.get('/').get_data(as_text=True)
    assert '<html lang="ko">' in korean and '나만의 Reboot 찾기' in korean
    assert 'name="csrf_token"' in korean
    assert client.post('/language', data={'language': 'invalid', 'csrf_token': csrf(client, '/')}).status_code == 400
    login(client)
    client.post('/language', data={'language': 'ko', 'csrf_token': csrf(client, '/'), 'next': '/products/'})
    client.delete_cookie('reboot_language')
    assert '<html lang="ko">' in client.get('/products/').get_data(as_text=True)
    with app.app_context():
        from core.models import Preference
        assert db.session.scalar(db.select(Preference)).language == 'ko'
    # Translated forms retain stable submitted SKU/flavor values and valid CSRF tokens.
    assert add_item(client).status_code == 302
    assert client.post('/shop/checkout', data=checkout(client)).status_code == 302



def test_brand_logo_and_seo_files(client):
    html = client.get('/').get_data(as_text=True)
    assert 'core/img/reboot-logo-on-dark.webp' in html and 'og:image' in html and 'core/img/favicon.png' in html
    for path in ['/static/core/img/reboot-logo-on-dark.webp', '/static/core/img/favicon.png', '/static/core/js/game.js', '/media/brand/reboot_og.jpg']:
        assert client.get(path).status_code == 200, path
    assert 'Disallow: /admin/' in client.get('/robots.txt').get_data(as_text=True)
    sitemap = client.get('/sitemap.xml')
    assert sitemap.mimetype == 'application/xml' and b'/products/jelly-balance' in sitemap.data and b'/admin' not in sitemap.data


def test_game_score_activity(client, app):
    assert client.post('/activity', json={'event': 'game_score', 'value': '120:Lime'}).status_code in (302, 400)
    login(client)
    token = csrf(client, '/game/')
    assert client.post('/activity', json={'event': 'game_score', 'value': '120:Lime'}, headers={'X-CSRFToken': token}).status_code == 204
    with app.app_context():
        assert db.session.scalar(db.select(Activity).where(Activity.event == 'game_score')).detail == {'value': '120:Lime'}


def test_admin_creator_links(client, app):
    data = {'code': 'newwave1', 'influencer_name': 'New Wave (fictional)', 'platform': 'TikTok', 'discount_percent': '12.5', 'commission_percent': '0', 'is_active': 'y'}
    assert client.get('/admin/links').status_code == 302
    login(client)
    assert client.get('/admin/links').status_code == 403
    assert client.post('/admin/links', data={**data, 'csrf_token': csrf(client, '/')}).status_code == 403
    logout(client)
    login(client, 'admin@example.com')
    assert client.post('/admin/links', data=data).status_code == 400
    assert client.post('/admin/links', data={**data, 'csrf_token': csrf(client, '/admin/links')}).status_code == 302
    for bad in [{'code': 'NEWWAVE1'}, {'code': 'bad code!'}, {'code': 'OK123', 'discount_percent': '80'}, {'code': 'OK124', 'commission_percent': ''}]:
        assert client.post('/admin/links', data={**data, **bad, 'csrf_token': csrf(client, '/admin/links')}).status_code == 400, bad
    with app.app_context():
        link = db.session.scalar(db.select(ReferralLink).where(ReferralLink.code == 'NEWWAVE1'))
        assert link.discount_rate == Decimal('0.125') and link.commission_rate == 0 and link.is_active and link.clicks == 0
        link_id = link.id
        assert db.session.scalar(db.select(Activity).where(Activity.event == 'referral_link_created'))
    assert 'NEWWAVE1' in client.get('/admin/links').get_data(as_text=True)
    edit = {**data, 'code': 'HACKED', 'influencer_name': 'Renamed', 'discount_percent': '10', 'commission_percent': '15', 'is_active': '', 'csrf_token': csrf(client, f'/admin/links/{link_id}')}
    assert client.post(f'/admin/links/{link_id}', data=edit).status_code == 302
    with app.app_context():
        link = db.session.get(ReferralLink, link_id)
        assert link.code == 'NEWWAVE1' and link.influencer_name == 'Renamed' and link.commission_rate == Decimal('0.15') and not link.is_active
    assert client.get('/admin/links/99999').status_code == 404
    logout(client)
    assert client.get('/r/NEWWAVE1').status_code == 404


def test_home_flavor_ring(client):
    html = client.get('/').get_data(as_text=True)
    assert 'data-flavor-carousel' in html and 'core/js/flavor-carousel.js' in html
    assert html.count('class="flavor-item"') == 12 and html.count('data-thumb=') == 12
    assert '/products/drink-balance?flavor=Cherry' in html
    for slug in ['drink-original-lime', 'jelly-balance-cherry']:
        for image in ['center', 'side', 'side-left']:
            assert client.get(f'/static/core/img/carousel/{slug}/{image}.webp').status_code == 200


def test_home_stage_and_spritz_demo(client):
    html = client.get('/').get_data(as_text=True)
    assert 'class="stage"' in html and html.count('class="mega-line"') == 4 and html.count('data-go=') == 4
    assert html.count('class="panel"') + html.count('class="panel is-on"') == 4 and html.count('class="note ') == 3
    assert 'data-plate' in html and 'id="plate-mist"' in html and html.count('<li>') >= 20
    for path in ['/static/core/home/styles.css', '/static/core/home/app.js', '/static/core/img/stage/bottle-lime-34.webp', '/static/core/img/stage/lineup.webp']:
        assert client.get(path).status_code == 200, path


def test_product_detail_has_no_ghost_text(client):
    for slug in ['drink-original', 'jelly-balance']:
        assert 'detail-ghost' not in client.get(f'/products/{slug}').get_data(as_text=True)



def test_home_jellies_dive_into_bottle(client):
    html = client.get('/').get_data(as_text=True)
    assert html.count('class="dive-jelly"') == 3 and 'data-melt' not in html
    assert all(f'data-shot="0-{k}"' in html for k in range(3))
    for flavor in ['lime', 'lemon', 'cherry']:
        for name in [f'bottle-{flavor}-34', f'jelly-{flavor}-34']:
            assert client.get(f'/static/core/img/stage/{name}.webp').status_code == 200, name
