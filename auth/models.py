import hashlib
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from core.extensions import db, login_manager
from core.models import utcnow


class User(UserMixin, db.Model):
    __tablename__ = 'auth_user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(254), nullable=False, unique=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='customer')
    age_confirmed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=utcnow)
    __table_args__ = (db.CheckConstraint("role IN ('admin', 'customer')"),)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return self.auth_token


class LoginSession(db.Model):
    __tablename__ = 'auth_session'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('auth_user.id'), nullable=False, index=True)
    token_hash = db.Column(db.String(64), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    revoked_at = db.Column(db.DateTime)
    user = db.relationship('User')


class LoginAttempt(db.Model):
    __tablename__ = 'auth_login_attempt'
    id = db.Column(db.Integer, primary_key=True)
    email_hash = db.Column(db.String(64), index=True, nullable=False)
    ip_hash = db.Column(db.String(64), index=True, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, index=True)


def token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()


@login_manager.user_loader
def load_user(token):
    row = db.session.scalar(db.select(LoginSession).where(LoginSession.token_hash == token_hash(token), LoginSession.revoked_at.is_(None), LoginSession.expires_at > utcnow()))
    if row:
        row.user.auth_token = token
        return row.user
    return None

