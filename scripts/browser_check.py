"""Run a real Chromium journey against an isolated database; never mutate the user's local DB."""
import os
import re
import secrets
import sys
import threading
import logging
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from playwright.sync_api import sync_playwright
from werkzeug.serving import make_server
from app import create_app
from core.extensions import db
from auth.seed import seed_accounts
from shop.seed import seed_products, seed_links, seed_dummy_orders

logging.getLogger('werkzeug').setLevel(logging.ERROR)


def screenshot_page(page, path):
    height = page.evaluate('document.documentElement.scrollHeight')
    for y in range(0, height, 650):
        page.evaluate('(y) => window.scrollTo(0, y)', y)
        page.wait_for_timeout(100)
    page.evaluate('Promise.all([...document.images].map(i => i.decode().catch(() => {})))')
    page.evaluate('window.scrollTo({top: 0, behavior: "instant"})')
    page.wait_for_timeout(300)
    page.screenshot(path=str(path), full_page=True)

out = ROOT / 'test-results'
out.mkdir(exist_ok=True)
db_path = out / ('browser-' + secrets.token_hex(5) + '.db')
password = secrets.token_urlsafe(18)
os.environ.update(ADMIN_EMAIL='browser-admin@example.com', ADMIN_PASSWORD=password, CUSTOMER_EMAIL='browser-customer@example.com', CUSTOMER_PASSWORD=password)
app = create_app({'TESTING': True, 'SECRET_KEY': secrets.token_hex(32), 'SQLALCHEMY_DATABASE_URI': 'sqlite:///' + db_path.as_posix(), 'SESSION_COOKIE_SECURE': False})
with app.app_context():
    db.create_all()
    seed_accounts()
    seed_products()
    seed_links()
    seed_dummy_orders()
    db.session.commit()
server = make_server('127.0.0.1', 5051, app, threaded=True)
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()

try:
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe', headless=True)
        context = browser.new_context(viewport={'width': 1440, 'height': 1000}, device_scale_factor=1)
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto('http://127.0.0.1:5051/', wait_until='networkidle')
        page.evaluate('document.fonts.ready')
        page.screenshot(path=str(out / 'home-viewport.png'))
        screenshot_page(page, out / 'home-desktop.png')
        page.get_by_role('button', name='Lemon', exact=True).click()
        assert 'lemon_flavored' in page.locator('#hero-bottle').get_attribute('src')
        page.locator('.hero-bottom .motion-toggle').click()
        assert page.locator('html').evaluate('(e) => e.classList.contains("motion-paused")')
        page.goto('http://127.0.0.1:5051/auth/login')
        page.get_by_label('Email address').fill(os.environ['CUSTOMER_EMAIL'])
        page.get_by_label('Password', exact=True).fill(password)
        page.get_by_role('button', name='Let’s go').click()
        page.wait_for_url('**/');
        page.goto('http://127.0.0.1:5051/r/NEONNIGHTS')
        page.goto('http://127.0.0.1:5051/products/drink-original?flavor=Cherry')
        page.get_by_label('Box of 3', exact=False).check()
        page.get_by_role('button', name='Increase quantity').click()
        page.screenshot(path=str(out / 'product-desktop.png'), full_page=True)
        page.get_by_role('button', name='Add to bag').click()
        page.wait_for_url('**/shop/cart')
        assert '$34.20' in page.locator('body').inner_text()
        page.get_by_role('link', name='Continue to checkout').click()
        page.get_by_label('Full name').fill('Browser Customer')
        page.get_by_label('City', exact=True).fill('Sample City')
        page.get_by_label('State', exact=True).select_option('CA')
        page.get_by_label('I understand this is a mock order.', exact=False).check()
        page.get_by_role('button', name='Place order (mock)').click()
        page.wait_for_url(re.compile(r'.*/shop/orders/\d+$'))
        assert 'No payment was taken' in page.locator('body').inner_text()
        page.goto('http://127.0.0.1:5051/vibe-test/')
        page.get_by_text('Out & about', exact=True).click()
        page.get_by_role('button', name='Next question').click()
        page.get_by_text('Make it a bite', exact=True).click()
        page.get_by_role('button', name='Next question').click()
        page.locator('input[value="Lemon"]').check()
        page.get_by_role('button', name='Show my Reboot').click()
        assert 'Your flavor: Lemon' in page.locator('body').inner_text()
        page.get_by_role('button', name='Logout', exact=True).click()
        page.goto('http://127.0.0.1:5051/auth/login')
        page.get_by_label('Email address').fill(os.environ['ADMIN_EMAIL'])
        page.get_by_label('Password', exact=True).fill(password)
        page.get_by_role('button', name='Let’s go').click()
        page.wait_for_url('**/admin/')
        page.goto('http://127.0.0.1:5051/admin/?start=2026-01-01&end=2026-10-23&status=paid&source=all')
        page.screenshot(path=str(out / 'admin-desktop.png'), full_page=True)
        with page.expect_download() as info:
            page.get_by_role('link', name='All matching orders CSV').click()
        download = info.value
        download.save_as(str(out / 'browser-orders.csv'))
        assert (out / 'browser-orders.csv').read_bytes().startswith(b'\xef\xbb\xbf')
        page.goto('http://127.0.0.1:5051/admin/activity')
        assert 'order_placed' in page.locator('body').inner_text().lower()
        mobile = browser.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=1, is_mobile=True, has_touch=True)
        mp = mobile.new_page()
        mp.on('pageerror', lambda error: errors.append(str(error)))
        for path in ['/', '/products/', '/products/jelly-balance', '/auth/register', '/contact/', '/vibe-test/']:
            mp.goto('http://127.0.0.1:5051' + path, wait_until='networkidle')
            assert mp.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'), f'Mobile overflow on {path}'
            if path == '/':
                mp.screenshot(path=str(out / 'home-mobile-viewport.png'))
                screenshot_page(mp, out / 'home-mobile.png')
                mp.get_by_role('button', name='Open menu', exact=True).click()
                assert mp.locator('#mobile-nav').is_visible()
                mp.get_by_role('button', name='Close menu', exact=True).click()
            if path == '/products/':
                mp.get_by_role('button', name='Jellies', exact=True).click()
                assert mp.locator('.product-grid .product-card:visible').count() == 2
        assert not errors, errors
        mp.goto('http://127.0.0.1:5051/')
        mp.get_by_role('button', name='한국어', exact=True).click()
        mp.wait_for_load_state('networkidle')
        assert mp.locator('html').get_attribute('lang') == 'ko'
        assert '나만의 Reboot 찾기' in mp.locator('body').inner_text()
        assert mp.evaluate('document.documentElement.scrollWidth <= innerWidth + 1')
        mp.screenshot(path=str(out / 'home-mobile-ko.png'))
        mp.goto('http://127.0.0.1:5051/auth/register')
        mp.get_by_label('이름', exact=True).fill('한국어 테스트')
        mp.get_by_label('이메일 주소', exact=True).fill('korean-browser@example.com')
        mp.get_by_label('비밀번호', exact=True).fill(password)
        mp.get_by_label('비밀번호 확인', exact=True).fill(password)
        mp.get_by_label('만 21세 이상이며', exact=False).check()
        mp.get_by_role('button', name='회원가입', exact=False).click()
        mp.wait_for_url('**/')
        mp.get_by_role('button', name='메뉴 열기', exact=True).click()
        mp.locator('.mobile-logout button').click()
        mp.wait_for_url('**/')
        mp.get_by_role('button', name='English', exact=True).click()
        mp.wait_for_load_state('networkidle')
        assert mp.locator('html').get_attribute('lang') == 'en'
        for width in (320, 768, 1024):
            mp.set_viewport_size({'width': width, 'height': 900})
            mp.goto('http://127.0.0.1:5051/')
            assert mp.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'), f'Homepage overflow at {width}'
        browser.close()
        print('Browser PASS: desktop/mobile, flavors, login/logout, referral checkout, quiz, admin CSV, menu, filters, English/Korean, Korean registration, responsive 320/390/768/1024/1440px, no JavaScript errors.')
finally:
    server.shutdown()
    thread.join(timeout=5)
    with app.app_context():
        db.session.remove()
        db.engine.dispose()
