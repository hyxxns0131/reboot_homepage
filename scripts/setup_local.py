"""Create local, untracked configuration without embedding credentials in source."""
import secrets
from pathlib import Path

root = Path(__file__).resolve().parents[1]
target = root / '.env'
if target.exists():
    print('Existing .env preserved.')
else:
    content = '\n'.join([
        'SECRET_KEY=' + secrets.token_hex(32),
        'ADMIN_EMAIL=admin@reboot.example.com',
        'ADMIN_PASSWORD=' + secrets.token_urlsafe(18),
        'CUSTOMER_EMAIL=customer@reboot.example.com',
        'CUSTOMER_PASSWORD=' + secrets.token_urlsafe(18),
        'DATABASE_URL=',
        'SITE_URL=http://127.0.0.1:5000',
        'SEED_DUMMY_DATA=1',
        'COOKIE_SECURE=0',
    ])
    target.write_text(content + '\n', encoding='utf-8')
    print('Local .env created. Open it privately to read the two generated account passwords.')

