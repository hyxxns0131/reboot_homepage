import os
from core.extensions import db
from core.models import utcnow
from auth.models import User


def seed_accounts():
    for prefix, role, name in [('ADMIN', 'admin', 'Reboot Admin'), ('CUSTOMER', 'customer', 'Reboot Explorer')]:
        email, password = os.environ.get(f'{prefix}_EMAIL', '').strip().lower(), os.environ.get(f'{prefix}_PASSWORD', '')
        if not email or len(password) < 8:
            raise ValueError(f'Set {prefix}_EMAIL and {prefix}_PASSWORD (at least 8 characters) in your environment.')
        existing = db.session.scalar(db.select(User).where(User.email == email))
        if existing:
            if existing.role != role:
                raise ValueError(f'{prefix}_EMAIL is already assigned to a different account role.')
            continue
        user = User(email=email, name=name, role=role, age_confirmed_at=utcnow())
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

