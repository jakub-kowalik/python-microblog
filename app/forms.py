from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length

from app.models import User


class LoginForm(FlaskForm):
    username = StringField('Nazwa użytkownika', validators=[DataRequired()])
    password = PasswordField('Hasło', validators=[DataRequired()])
    remember_me = BooleanField('Zapamiętaj mnie')
    submit = SubmitField('Zaloguj się')


class RegistrationForm(FlaskForm):
    username = StringField('Nazwa użytkownika', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Hasło', validators=[DataRequired()])
    password2 = PasswordField(
        'Powtorz hasło', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Zarejestruj')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Ta nazwa użytkownika jest już zajęta.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Adres email nieprawidłowy.')


class EditProfileForm(FlaskForm):
    about_me = TextAreaField('O mnie', validators=[Length(min=0, max=140)])
    submit = SubmitField('Zatwierdź')

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username


class EmptyForm(FlaskForm):
    submit = SubmitField('Zatwierdź')


class CheckboxForm(FlaskForm):
    checkbox = BooleanField('Delete posts')
    submit = SubmitField('Submit')


class PostForm(FlaskForm):
    post = TextAreaField('Powiedz cos od siebie', validators=[
        DataRequired(), Length(min=1, max=1000)])
    submit = SubmitField('Submit')
