import secrets
from datetime import timedelta
from urllib.parse import urlsplit, unquote
from flask import render_template, redirect, request, url_for, flash, session, abort
from flask_login import current_user, login_user, logout_user, login_required
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash
from auth import bp
from auth.models import User, LoginSession, LoginAttempt, token_hash
from auth.forms import LoginForm, RegisterForm
from core.extensions import db
from core.models import utcnow
from core.activity import record

DUMMY_HASH = generate_password_hash(secrets.token_urlsafe(32))


def safe_next(value):
    value = unquote(value or '')
    parsed = urlsplit(value)
    return value if value.startswith('/') and not value.startswith('//') and not parsed.scheme and not parsed.netloc and '\\' not in value and not any(ord(c) < 32 for c in value) else None


def establish_session(user, remember=False):
    session.clear()
    token = secrets.token_urlsafe(32)
    user.auth_token = token
    db.session.add(LoginSession(user_id=user.id, token_hash=token_hash(token), expires_at=utcnow() + timedelta(days=30 if remember else 1)))
    login_user(user, remember=remember)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard') if current_user.role == 'admin' else url_for('main.home'))
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        email_digest, ip_digest = token_hash(email), token_hash(request.remote_addr or 'unknown')
        since = utcnow() - timedelta(minutes=15)
        attempts = db.session.scalar(db.select(db.func.count()).select_from(LoginAttempt).where(LoginAttempt.created_at > since, db.or_(LoginAttempt.email_hash == email_digest, LoginAttempt.ip_hash == ip_digest)))
        if attempts >= 10:
            flash('Too many attempts. Please try again in 15 minutes.', 'error')
            return render_template('auth/form.html', form=form, register=False), 429
        user = db.session.scalar(db.select(User).where(User.email == email))
        valid = check_password_hash(user.password_hash if user else DUMMY_HASH, form.password.data)
        if user and valid:
            establish_session(user, form.remember.data)
            record('login', user_id=user.id)
            db.session.commit()
            flash('Welcome back. Your next chapter starts here.', 'success')
            return redirect(safe_next(request.args.get('next')) or (url_for('admin.dashboard') if user.role == 'admin' else url_for('main.home')))
        db.session.add(LoginAttempt(email_hash=email_digest, ip_hash=ip_digest))
        db.session.commit()
        flash('Email or password is incorrect.', 'error')
    return render_template('auth/form.html', form=form, register=False)


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(name=form.name.data.strip(), email=form.email.data.strip().lower(), role='customer', age_confirmed_at=utcnow())
        user.set_password(form.password.data)
        try:
            db.session.add(user)
            db.session.flush()
        except IntegrityError:
            db.session.rollback()
            form.email.errors.append('This email is already registered. Please sign in.')
            return render_template('auth/form.html', form=form, register=True), 400
        establish_session(user)
        record('register', user_id=user.id)
        db.session.commit()
        flash('You’re in. Welcome to the Reboot crew.', 'success')
        return redirect(safe_next(request.args.get('next')) or url_for('main.home'))
    return render_template('auth/form.html', form=form, register=True)


@bp.post('/logout')
@login_required
def logout():
    row = db.session.scalar(db.select(LoginSession).where(LoginSession.token_hash == token_hash(current_user.auth_token)))
    if row:
        row.revoked_at = utcnow()
    record('logout')
    db.session.commit()
    logout_user()
    session.clear()
    flash('You’re signed out. See you next time.', 'success')
    return redirect(url_for('main.home'))

