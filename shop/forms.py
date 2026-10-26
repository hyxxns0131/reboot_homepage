from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, HiddenField, BooleanField
from wtforms.validators import DataRequired, Length

STATES = 'AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY'.split()


class CheckoutForm(FlaskForm):
    name = StringField('Full name', validators=[DataRequired(), Length(min=2, max=100)])
    city = StringField('City', validators=[DataRequired(), Length(min=2, max=100)])
    state = SelectField('State', choices=[('', 'Select a state')] + [(s, s) for s in STATES], validators=[DataRequired()])
    checkout_token = HiddenField(validators=[DataRequired(), Length(max=64)])
    acknowledge = BooleanField('I understand this is a mock order. No payment will be taken and no products will be shipped.', validators=[DataRequired()])

