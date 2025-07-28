from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, FloatField, DateField, SubmitField, PasswordField, BooleanField, SelectField
from wtforms.validators import DataRequired, Length, NumberRange, Email, EqualTo, ValidationError
from models import User

class MedicineForm(FlaskForm):
    name = StringField('Medicine Name', validators=[DataRequired(), Length(min=2, max=100)])
    batch_number = StringField('Batch Number', validators=[DataRequired(), Length(min=2, max=50)])
    category = StringField('Category', validators=[DataRequired(), Length(min=2, max=50)])
    quantity = IntegerField('Quantity', validators=[DataRequired(), NumberRange(min=0)])
    expiry_date = DateField('Expiry Date', validators=[DataRequired()])
    price = FloatField('Price', validators=[DataRequired(), NumberRange(min=0)])
    gst_percent = FloatField('GST Percent', validators=[DataRequired(), NumberRange(min=0, max=100)])
    submit = SubmitField('Submit')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=[('Admin', 'Admin'), ('Pharmacist', 'Pharmacist'), ('Sales', 'Sales')], validators=[DataRequired()])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class SaleForm(FlaskForm):
    customer = SelectField('Customer', coerce=int, validators=[DataRequired()])
    medicine = SelectField('Medicine', coerce=int, validators=[DataRequired()])
    quantity = IntegerField('Quantity', validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField('Add to Cart')

class CustomerForm(FlaskForm):
    name = StringField('Customer Name', validators=[DataRequired(), Length(min=2, max=100)])
    phone_number = StringField('Phone Number', validators=[Length(max=20)])
    email = StringField('Email', validators=[Email(), Length(max=100)])
    address = StringField('Address', validators=[Length(max=200)])
    submit = SubmitField('Submit')
