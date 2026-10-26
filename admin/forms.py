from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DecimalField, BooleanField
from wtforms.validators import DataRequired, Length, NumberRange, Regexp

PLATFORMS = ['TikTok', 'Instagram', 'YouTube', 'Other']


class ReferralLinkForm(FlaskForm):
    code = StringField('Link code', validators=[DataRequired(), Length(min=3, max=40), Regexp(r'^[A-Za-z0-9]+$', message='Use letters and numbers only.')])
    influencer_name = StringField('Creator name', validators=[DataRequired(), Length(min=2, max=100)])
    platform = SelectField('Platform', choices=[(p, p) for p in PLATFORMS], validators=[DataRequired()])
    discount_percent = DecimalField('Customer discount (%)', places=2, validators=[DataRequired(message='Enter 0 or more.'), NumberRange(min=0, max=50)])
    commission_percent = DecimalField('Creator commission (%)', places=2, validators=[DataRequired(message='Enter 0 or more.'), NumberRange(min=0, max=50)])
    is_active = BooleanField('Link is active', default=True)
