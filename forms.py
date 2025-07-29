from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, FloatField, DateField, SubmitField, PasswordField, BooleanField, SelectField, FormField, FieldList
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

class PasswordResetRequestForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    submit = SubmitField('Request Password Reset')

class PasswordResetForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')

class SaleItemForm(FlaskForm):
    medicine = SelectField('Medicine', coerce=int, validators=[DataRequired()])
    quantity = IntegerField('Quantity', validators=[DataRequired(), NumberRange(min=1)])

class SaleForm(FlaskForm):
    customer = SelectField('Customer', coerce=int, validators=[DataRequired()])
    items = FieldList(FormField(SaleItemForm), min_entries=1)
    submit = SubmitField('Create Sale')

class CustomerForm(FlaskForm):
    name = StringField('Customer Name', validators=[DataRequired(), Length(min=2, max=100)])
    phone_number = StringField('Phone Number', validators=[Length(max=20)])
    email = StringField('Email', validators=[Email(), Length(max=100)])
    address = StringField('Address', validators=[Length(max=200)])
    submit = SubmitField('Submit')

class SupplierForm(FlaskForm):
    name = StringField('Supplier Name', validators=[DataRequired(), Length(min=2, max=100)])
    contact_person = StringField('Contact Person', validators=[Length(max=100)])
    phone_number = StringField('Phone Number', validators=[Length(max=20)])
    email = StringField('Email', validators=[Email(), Length(max=100)])
    address = StringField('Address', validators=[Length(max=200)])
    submit = SubmitField('Submit')

class PurchaseItemForm(FlaskForm):
    medicine = SelectField('Medicine', coerce=int, validators=[DataRequired()])
    quantity = IntegerField('Quantity', validators=[DataRequired(), NumberRange(min=1)])
    price_per_unit = FloatField('Price per Unit', validators=[DataRequired(), NumberRange(min=0)])

class PurchaseForm(FlaskForm):
    supplier = SelectField('Supplier', coerce=int, validators=[DataRequired()])
    items = FieldList(FormField(PurchaseItemForm), min_entries=1)
    submit = SubmitField('Create Purchase')
