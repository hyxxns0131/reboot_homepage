import re
import secrets
import pytest
from app import create_app
from core.extensions import db
from auth.models import User
from auth.seed import seed_accounts
from shop.seed import seed_products, seed_links

TEST_PASSWORD = 'Test-fixture-only-123!'


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv('ADMIN_EMAIL', 'admin@example.com')
    monkeypatch.setenv('ADMIN_PASSWORD', TEST_PASSWORD)
    monkeypatch.setenv('CUSTOMER_EMAIL', 'customer@example.com')
    monkeypatch.setenv('CUSTOMER_PASSWORD', TEST_PASSWORD)
    monkeypatch.setenv('SEED_DUMMY_DATA', '0')
    app = create_app({'TESTING': True, 'SECRET_KEY': secrets.token_hex(32), 'SQLALCHEMY_DATABASE_URI': f'sqlite:///{(tmp_path / "test.db").as_posix()}', 'SESSION_COOKIE_SECURE': False})
    with app.app_context():
        db.create_all()
        seed_accounts()
        seed_products()
        seed_links()
        db.session.commit()
    yield app
    with app.app_context():
        db.session.remove()
        db.engine.dispose()


@pytest.fixture
def client(app):
    return app.test_client()


def csrf(client, path='/auth/login'):
    response = client.get(path)
    assert response.status_code == 200, (path, response.status_code)
    return re.search(r'name="csrf-token" content="([^"]+)"', response.get_data(as_text=True)).group(1)


def login(client, email='customer@example.com', remember=False, next_path=''):
    response = client.post('/auth/login' + next_path, data={'csrf_token': csrf(client), 'email': email, 'password': TEST_PASSWORD, 'remember': 'y' if remember else ''})
    assert response.status_code == 302
    return response


def logout(client):
    return client.post('/auth/logout', data={'csrf_token': csrf(client, '/')})


def add_item(client, sku='drink-original-box3', flavor='Lime', quantity=2):
    return client.post('/shop/cart/add', data={'csrf_token': csrf(client, '/shop/cart'), 'sku': sku, 'flavor': flavor, 'quantity': quantity, 'price': '.01'})


def checkout(client):
    response = client.get('/shop/checkout')
    html = response.get_data(as_text=True)
    token = re.search(r'name="checkout_token"[^>]*value="([^"]+)"', html).group(1)
    csrf_token = re.search(r'name="csrf-token" content="([^"]+)"', html).group(1)
    return {'csrf_token': csrf_token, 'checkout_token': token, 'name': 'Test Customer', 'city': 'Sample City', 'state': 'CA', 'acknowledge': 'y'}

