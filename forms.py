from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, FloatField, DateField, SubmitField, PasswordField, BooleanField, SelectField, FormField, FieldList, TextAreaField
from wtforms.validators import DataRequired, Length, NumberRange, Email, EqualTo, ValidationError, Optional
from models import User

class MedicineForm(FlaskForm):
    name = StringField('Medicine Name', validators=[DataRequired(), Length(min=2, max=100)])
    batch_number = StringField('Batch Number', validators=[DataRequired(), Length(min=2, max=50)])
    category = StringField('Category', validators=[DataRequired(), Length(min=2, max=50)])
    quantity = IntegerField('Quantity', validators=[DataRequired(), NumberRange(min=0)])
    expiry_date = DateField('Expiry Date', validators=[DataRequired()])
    price = FloatField('Selling Price', validators=[DataRequired(), NumberRange(min=0)])
    cost_price = FloatField('Cost Price', validators=[Optional(), NumberRange(min=0)])
    gst_percent = FloatField('GST Percent', validators=[DataRequired(), NumberRange(min=0, max=100)])
    
    # Enhanced inventory fields
    minimum_stock_level = IntegerField('Minimum Stock Level', validators=[DataRequired(), NumberRange(min=0)], default=10)
    maximum_stock_level = IntegerField('Maximum Stock Level', validators=[DataRequired(), NumberRange(min=1)], default=1000)
    reorder_point = IntegerField('Reorder Point', validators=[DataRequired(), NumberRange(min=0)], default=5)
    location = StringField('Storage Location', validators=[Optional(), Length(max=100)])
    unit_of_measurement = SelectField('Unit', 
                                    choices=[('Units', 'Units'), ('Boxes', 'Boxes'), ('Bottles', 'Bottles'), 
                                            ('Strips', 'Strips'), ('Vials', 'Vials'), ('Tablets', 'Tablets')], 
                                    validators=[DataRequired()])
    manufacturer = StringField('Manufacturer', validators=[Optional(), Length(max=100)])
    supplier_id = SelectField('Supplier', coerce=int, validators=[Optional()])
    last_restocked_date = DateField('Last Restocked Date', validators=[Optional()])
    
    submit = SubmitField('Submit')
    
    def __init__(self, *args, **kwargs):
        super(MedicineForm, self).__init__(*args, **kwargs)
        # Populate supplier choices
        from models import Supplier
        self.supplier_id.choices = [(0, 'Select Supplier')] + [(s.id, s.name) for s in Supplier.query.order_by('name').all()]

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    # Only allow Pharmacist and Customer roles in registration
    role = SelectField('Role', choices=[('Pharmacist', 'Pharmacist'), ('Customer', 'Customer')], validators=[DataRequired()])
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

class PatientForm(FlaskForm):
    # Personal Information
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=2, max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=50)])
    date_of_birth = DateField('Date of Birth', validators=[DataRequired()])
    gender = SelectField('Gender', choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], validators=[DataRequired()])
    phone_number = StringField('Phone Number', validators=[Optional(), Length(max=20)])
    email = StringField('Email', validators=[Optional(), Email(), Length(max=100)])
    address = TextAreaField('Address', validators=[Optional(), Length(max=500)])
    
    # Insurance Information
    insurance_provider = StringField('Insurance Provider', validators=[Optional(), Length(max=100)])
    insurance_policy_number = StringField('Policy Number', validators=[Optional(), Length(max=50)])
    insurance_group_number = StringField('Group Number', validators=[Optional(), Length(max=50)])
    insurance_expiry_date = DateField('Insurance Expiry Date', validators=[Optional()])
    
    # Emergency Contact
    emergency_contact_name = StringField('Emergency Contact Name', validators=[Optional(), Length(max=100)])
    emergency_contact_relationship = StringField('Relationship', validators=[Optional(), Length(max=50)])
    emergency_contact_phone = StringField('Emergency Contact Phone', validators=[Optional(), Length(max=20)])
    emergency_contact_email = StringField('Emergency Contact Email', validators=[Optional(), Email(), Length(max=100)])
    
    # Medical Information
    blood_group = SelectField('Blood Group', 
                             choices=[('', 'Select Blood Group'), ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'), 
                                     ('O+', 'O+'), ('O-', 'O-'), ('AB+', 'AB+'), ('AB-', 'AB-')], 
                             validators=[Optional()])
    allergies = TextAreaField('Allergies', validators=[Optional(), Length(max=1000)])
    chronic_conditions = TextAreaField('Chronic Conditions', validators=[Optional(), Length(max=1000)])
    current_medications = TextAreaField('Current Medications', validators=[Optional(), Length(max=1000)])
    
    submit = SubmitField('Submit')

class MedicalHistoryForm(FlaskForm):
    # Visit Information
    visit_date = DateField('Visit Date', validators=[DataRequired()])
    chief_complaint = TextAreaField('Chief Complaint', validators=[Optional(), Length(max=500)])
    symptoms = TextAreaField('Symptoms', validators=[Optional(), Length(max=1000)])
    diagnosis = TextAreaField('Diagnosis', validators=[Optional(), Length(max=1000)])
    treatment = TextAreaField('Treatment', validators=[Optional(), Length(max=1000)])
    prescription = TextAreaField('Prescription', validators=[Optional(), Length(max=1000)])
    
    # Vital Signs
    temperature = FloatField('Temperature (°F)', validators=[Optional(), NumberRange(min=90, max=110)])
    blood_pressure_systolic = IntegerField('Blood Pressure (Systolic)', validators=[Optional(), NumberRange(min=50, max=250)])
    blood_pressure_diastolic = IntegerField('Blood Pressure (Diastolic)', validators=[Optional(), NumberRange(min=30, max=150)])
    heart_rate = IntegerField('Heart Rate (BPM)', validators=[Optional(), NumberRange(min=30, max=200)])
    weight = FloatField('Weight (kg)', validators=[Optional(), NumberRange(min=1, max=500)])
    height = FloatField('Height (cm)', validators=[Optional(), NumberRange(min=50, max=250)])
    
    # Additional Information
    doctor_name = StringField('Doctor Name', validators=[Optional(), Length(max=100)])
    notes = TextAreaField('Notes', validators=[Optional(), Length(max=2000)])
    follow_up_date = DateField('Follow-up Date', validators=[Optional()])
    
    submit = SubmitField('Submit')

class MedicalEquipmentForm(FlaskForm):
    # Basic Information
    name = StringField('Equipment Name', validators=[DataRequired(), Length(min=2, max=100)])
    model_number = StringField('Model Number', validators=[Optional(), Length(max=50)])
    serial_number = StringField('Serial Number', validators=[DataRequired(), Length(min=2, max=50)])
    category = SelectField('Category', 
                          choices=[('Diagnostic', 'Diagnostic Equipment'), ('Surgical', 'Surgical Instruments'),
                                  ('Laboratory', 'Laboratory Equipment'), ('Monitoring', 'Monitoring Devices'),
                                  ('Therapeutic', 'Therapeutic Equipment'), ('Furniture', 'Medical Furniture'),
                                  ('Other', 'Other Equipment')], 
                          validators=[DataRequired()])
    manufacturer = StringField('Manufacturer', validators=[Optional(), Length(max=100)])
    
    # Purchase Information
    purchase_date = DateField('Purchase Date', validators=[Optional()])
    purchase_price = FloatField('Purchase Price', validators=[Optional(), NumberRange(min=0)])
    supplier_id = SelectField('Supplier', coerce=int, validators=[Optional()])
    warranty_expiry = DateField('Warranty Expiry', validators=[Optional()])
    
    # Status and Location
    status = SelectField('Status', 
                        choices=[('Active', 'Active'), ('Maintenance', 'Under Maintenance'), 
                                ('Retired', 'Retired'), ('Damaged', 'Damaged')], 
                        validators=[DataRequired()], default='Active')
    location = StringField('Location', validators=[Optional(), Length(max=100)])
    
    # Maintenance
    last_maintenance_date = DateField('Last Maintenance Date', validators=[Optional()])
    next_maintenance_date = DateField('Next Maintenance Date', validators=[Optional()])
    maintenance_frequency_days = IntegerField('Maintenance Frequency (Days)', 
                                            validators=[Optional(), NumberRange(min=1)], default=365)
    
    # Usage
    usage_hours = FloatField('Usage Hours', validators=[Optional(), NumberRange(min=0)], default=0.0)
    last_used_date = DateField('Last Used Date', validators=[Optional()])
    
    # Additional Information
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    notes = TextAreaField('Notes', validators=[Optional(), Length(max=1000)])
    
    submit = SubmitField('Submit')
    
    def __init__(self, *args, **kwargs):
        super(MedicalEquipmentForm, self).__init__(*args, **kwargs)
        # Populate supplier choices
        from models import Supplier
        self.supplier_id.choices = [(0, 'Select Supplier')] + [(s.id, s.name) for s in Supplier.query.order_by('name').all()]

class InventoryAlertForm(FlaskForm):
    alert_type = SelectField('Alert Type', 
                           choices=[('LOW_STOCK', 'Low Stock'), ('OUT_OF_STOCK', 'Out of Stock'),
                                   ('EXPIRED', 'Expired'), ('EXPIRING_SOON', 'Expiring Soon'),
                                   ('MAINTENANCE_DUE', 'Maintenance Due'), ('WARRANTY_EXPIRED', 'Warranty Expired')], 
                           validators=[DataRequired()])
    message = TextAreaField('Message', validators=[DataRequired(), Length(min=10, max=500)])
    severity = SelectField('Severity', 
                          choices=[('Low', 'Low'), ('Medium', 'Medium'), ('High', 'High'), ('Critical', 'Critical')], 
                          validators=[DataRequired()], default='Medium')
    submit = SubmitField('Create Alert')

class PrescriptionForm(FlaskForm):
    # Basic Information
    prescription_number = StringField('Prescription Number', validators=[DataRequired(), Length(min=5, max=50)])
    patient_id = SelectField('Patient', coerce=int, validators=[DataRequired()])
    
    # Doctor Information
    doctor_name = StringField('Doctor Name', validators=[DataRequired(), Length(min=2, max=100)])
    doctor_license = StringField('Doctor License Number', validators=[Optional(), Length(max=50)])
    doctor_contact = StringField('Doctor Contact', validators=[Optional(), Length(max=20)])
    clinic_name = StringField('Clinic/Hospital Name', validators=[Optional(), Length(max=100)])
    clinic_address = TextAreaField('Clinic Address', validators=[Optional(), Length(max=500)])
    
    # Medical Information
    diagnosis = TextAreaField('Diagnosis', validators=[Optional(), Length(max=1000)])
    symptoms = TextAreaField('Symptoms', validators=[Optional(), Length(max=1000)])
    patient_age = IntegerField('Patient Age', validators=[Optional(), NumberRange(min=0, max=150)])
    patient_weight = FloatField('Patient Weight (kg)', validators=[Optional(), NumberRange(min=1, max=500)])
    
    # Prescription Details
    prescription_date = DateField('Prescription Date', validators=[DataRequired()])
    valid_until = DateField('Valid Until', validators=[Optional()])
    priority = SelectField('Priority', 
                          choices=[('Normal', 'Normal'), ('Urgent', 'Urgent'), ('Emergency', 'Emergency')], 
                          validators=[DataRequired()], default='Normal')
    is_emergency = BooleanField('Emergency Prescription')
    
    # Insurance Information
    insurance_provider = StringField('Insurance Provider', validators=[Optional(), Length(max=100)])
    insurance_policy_number = StringField('Policy Number', validators=[Optional(), Length(max=50)])
    insurance_approval_number = StringField('Approval Number', validators=[Optional(), Length(max=50)])
    
    # Additional Information
    special_instructions = TextAreaField('Special Instructions', validators=[Optional(), Length(max=1000)])
    pharmacist_notes = TextAreaField('Pharmacist Notes', validators=[Optional(), Length(max=1000)])
    
    submit = SubmitField('Submit')
    
    def __init__(self, *args, **kwargs):
        super(PrescriptionForm, self).__init__(*args, **kwargs)
        # Populate patient choices
        from models import Patient
        self.patient_id.choices = [(p.id, p.full_name) for p in Patient.query.order_by(Patient.first_name, Patient.last_name).all()]

class PrescriptionItemForm(FlaskForm):
    medicine_id = SelectField('Medicine', coerce=int, validators=[Optional()])
    medicine_name = StringField('Medicine Name', validators=[DataRequired(), Length(min=2, max=100)])
    medicine_strength = StringField('Strength', validators=[Optional(), Length(max=50)])
    medicine_form = SelectField('Form', 
                               choices=[('Tablet', 'Tablet'), ('Capsule', 'Capsule'), ('Syrup', 'Syrup'), 
                                       ('Injection', 'Injection'), ('Cream', 'Cream'), ('Drops', 'Drops'), 
                                       ('Inhaler', 'Inhaler'), ('Ointment', 'Ointment'), ('Other', 'Other')], 
                               validators=[Optional()])
    
    # Prescription Details
    prescribed_quantity = IntegerField('Prescribed Quantity', validators=[DataRequired(), NumberRange(min=1)])
    unit = SelectField('Unit', 
                      choices=[('Units', 'Units'), ('Tablets', 'Tablets'), ('Capsules', 'Capsules'), 
                              ('ml', 'ml'), ('mg', 'mg'), ('Bottles', 'Bottles'), ('Tubes', 'Tubes')], 
                      validators=[DataRequired()])
    
    # Dosage Instructions
    dosage = StringField('Dosage', validators=[Optional(), Length(max=100)], render_kw={"placeholder": "e.g., 1 tablet"})
    frequency = StringField('Frequency', validators=[Optional(), Length(max=100)], render_kw={"placeholder": "e.g., twice daily"})
    duration = StringField('Duration', validators=[Optional(), Length(max=100)], render_kw={"placeholder": "e.g., for 7 days"})
    timing = StringField('Timing', validators=[Optional(), Length(max=100)], render_kw={"placeholder": "e.g., after meals"})
    route = SelectField('Route', 
                       choices=[('Oral', 'Oral'), ('Topical', 'Topical'), ('Injection', 'Injection'), 
                               ('Nasal', 'Nasal'), ('Eye', 'Eye'), ('Ear', 'Ear'), ('Other', 'Other')], 
                       validators=[Optional()])
    
    # Additional Instructions
    special_instructions = TextAreaField('Special Instructions', validators=[Optional(), Length(max=500)])
    substitution_allowed = BooleanField('Substitution Allowed', default=True)
    
    def __init__(self, *args, **kwargs):
        super(PrescriptionItemForm, self).__init__(*args, **kwargs)
        # Populate medicine choices
        from models import Medicine
        self.medicine_id.choices = [(0, 'Select Medicine')] + [(m.id, f"{m.name} - {m.batch_number}") for m in Medicine.query.order_by('name').all()]

class EnhancedSaleForm(FlaskForm):
    customer_id = SelectField('Customer', coerce=int, validators=[DataRequired()])
    prescription_id = SelectField('Prescription (Optional)', coerce=int, validators=[Optional()])
    
    # Payment and Billing
    payment_method = SelectField('Payment Method', 
                                choices=[('Cash', 'Cash'), ('Card', 'Debit/Credit Card'), ('UPI', 'UPI'), 
                                        ('Insurance', 'Insurance'), ('Mixed', 'Mixed Payment')], 
                                validators=[DataRequired()], default='Cash')
    payment_status = SelectField('Payment Status', 
                                choices=[('Paid', 'Paid'), ('Pending', 'Pending'), ('Partial', 'Partial')], 
                                validators=[DataRequired()], default='Paid')
    
    discount_amount = FloatField('Discount Amount', validators=[Optional(), NumberRange(min=0)], default=0.0)
    insurance_claim_amount = FloatField('Insurance Claim', validators=[Optional(), NumberRange(min=0)], default=0.0)
    patient_copay = FloatField('Patient Co-pay', validators=[Optional(), NumberRange(min=0)], default=0.0)
    
    # Sale Information
    sale_type = SelectField('Sale Type', 
                           choices=[('Direct Sale', 'Direct Sale'), ('Prescription Sale', 'Prescription Sale')], 
                           validators=[DataRequired()], default='Direct Sale')
    dispensed_by = StringField('Dispensed By', validators=[Optional(), Length(max=100)])
    notes = TextAreaField('Notes', validators=[Optional(), Length(max=500)])
    
    submit = SubmitField('Process Sale')
    
    def __init__(self, *args, **kwargs):
        super(EnhancedSaleForm, self).__init__(*args, **kwargs)
        # Populate customer and prescription choices
        from models import Customer, Prescription
        self.customer_id.choices = [(c.id, c.name) for c in Customer.query.order_by('name').all()]
        self.prescription_id.choices = [(0, 'No Prescription')] + [(p.id, f"{p.prescription_number} - {p.patient.full_name}") for p in Prescription.query.filter_by(status='Pending').order_by(Prescription.prescription_date.desc()).all()]

class DispenseForm(FlaskForm):
    prescription_id = SelectField('Prescription', coerce=int, validators=[DataRequired()])
    customer_id = SelectField('Customer', coerce=int, validators=[DataRequired()])
    
    # Payment Information
    payment_method = SelectField('Payment Method', 
                                choices=[('Cash', 'Cash'), ('Card', 'Debit/Credit Card'), ('UPI', 'UPI'), 
                                        ('Insurance', 'Insurance'), ('Mixed', 'Mixed Payment')], 
                                validators=[DataRequired()], default='Cash')
    discount_amount = FloatField('Discount Amount', validators=[Optional(), NumberRange(min=0)], default=0.0)
    insurance_claim_amount = FloatField('Insurance Claim', validators=[Optional(), NumberRange(min=0)], default=0.0)
    
    # Dispensing Information
    dispensed_by = StringField('Dispensed By', validators=[DataRequired(), Length(min=2, max=100)])
    dispensing_notes = TextAreaField('Dispensing Notes', validators=[Optional(), Length(max=500)])
    
    submit = SubmitField('Dispense Prescription')
    
    def __init__(self, *args, **kwargs):
        super(DispenseForm, self).__init__(*args, **kwargs)
        # Populate choices
        from models import Customer, Prescription
        self.customer_id.choices = [(c.id, c.name) for c in Customer.query.order_by('name').all()]
        self.prescription_id.choices = [(p.id, f"{p.prescription_number} - {p.patient.full_name}") for p in Prescription.query.filter(Prescription.status.in_(['Pending', 'Partially Dispensed'])).order_by(Prescription.prescription_date.desc()).all()]

class AdminUserForm(FlaskForm):
    """Admin form for user management - includes all roles"""
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    # Admin can create users with all roles
    role = SelectField('Role', choices=[('Admin', 'Admin'), ('Pharmacist', 'Pharmacist'), ('Customer', 'Customer')], validators=[DataRequired()])
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Create User')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')

class EditUserForm(FlaskForm):
    """Admin form for editing existing users"""
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    role = SelectField('Role', choices=[('Admin', 'Admin'), ('Pharmacist', 'Pharmacist'), ('Customer', 'Customer')], validators=[DataRequired()])
    is_active = BooleanField('Active')
    change_password = BooleanField('Change Password')
    password = PasswordField('New Password')
    confirm_password = PasswordField('Confirm New Password', validators=[EqualTo('password')])
    submit = SubmitField('Update User')

    def __init__(self, original_username, *args, **kwargs):
        super(EditUserForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('That username is taken. Please choose a different one.')
