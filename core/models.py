from datetime import datetime, timezone
from core.extensions import db


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Activity(db.Model):
    __tablename__ = 'core_activity'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('auth_user.id'), index=True)
    event = db.Column(db.String(60), nullable=False, index=True)
    path = db.Column(db.String(250))
    detail = db.Column(db.JSON, default=dict)
    created_at = db.Column(db.DateTime, default=utcnow, index=True)
    user = db.relationship('User')


class Submission(db.Model):
    __tablename__ = 'core_submission'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('auth_user.id'))
    kind = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(254), nullable=False)
    subject = db.Column(db.String(200))
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow)


class QuizResult(db.Model):
    __tablename__ = 'vibe_result'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('auth_user.id'))
    answers = db.Column(db.JSON, nullable=False)
    product_slug = db.Column(db.String(60), nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow)


class Preference(db.Model):
    __tablename__ = 'core_preference'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('auth_user.id'), nullable=False, index=True)
    language = db.Column(db.String(2), nullable=False, default='en')
    __table_args__ = (db.UniqueConstraint('user_id'), db.CheckConstraint("language IN ('en', 'ko')"))

