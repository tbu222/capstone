from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, IntegerField, DecimalField
from wtforms.validators import DataRequired, Email, Length
from flask_wtf.file import FileAllowed, FileField, FileRequired

class UserAddForm(FlaskForm):
    """Form for adding users."""

    username = StringField('Username', validators=[DataRequired()])
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[Length(min=6)])
    image_url = StringField('(Optional) Image URL')


class UserEditForm(FlaskForm):
    """Form for editing users."""

    username = StringField('Username', validators=[DataRequired()])
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    image_url = StringField('(Optional) Image URL')
    header_image_url = StringField('(Optional) Header Image URL')
    bio = TextAreaField('(Optional) Tell us about yourself')
    password = PasswordField('Password', validators=[Length(min=6)])


class LoginForm(FlaskForm):
    """Login form."""

    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[Length(min=6)])

class ProductAddForm(FlaskForm):
    """Form for adding product."""
    name = StringField('Name', validators=[DataRequired()])
    price = DecimalField('Price', validators=[DataRequired()])
    discount = IntegerField('Discount', default=0)
    stock = IntegerField('Stock', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    colors = TextAreaField('Colors', validators=[DataRequired()])

    image_1= FileField('Image 1', validators=[FileAllowed(['jpg','png','jpeg','gif']), 'Image only'])
    image_2= FileField('Image 2', validators=[FileAllowed(['jpg','png','jpeg','gif']), 'Image only'])
    image_3= FileField('Image 3', validators=[FileAllowed(['jpg','png','jpeg','gif']), 'Image only'])