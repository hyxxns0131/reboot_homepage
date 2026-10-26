from flask import request
from flask_login import current_user
from core.extensions import db
from core.models import Activity


def record(event, detail=None, user_id=None):
    if user_id is None and current_user.is_authenticated:
        user_id = current_user.id
    db.session.add(Activity(user_id=user_id, event=event, path=request.path[:250], detail=detail or {}))

