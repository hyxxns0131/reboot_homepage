from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, Email, Length


class ContactForm(FlaskForm):
    name = StringField('Your name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email address', validators=[DataRequired(), Email(), Length(max=254)])
    subject = StringField('Subject', validators=[DataRequired(), Length(min=2, max=200)])
    message = TextAreaField('Your message', validators=[DataRequired(), Length(min=10, max=4000)])
    consent = BooleanField('I agree to the Privacy Policy and to being contacted about this request.', validators=[DataRequired()])

