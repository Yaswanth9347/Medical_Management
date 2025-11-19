from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='Customer')  # Default role is Customer
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'
    
    # Role checking methods
    def is_admin(self):
        """Check if user has admin role"""
        return self.role == 'Admin'
    
    def is_pharmacist(self):
        """Check if user has pharmacist role"""
        return self.role == 'Pharmacist'
    
    def is_customer(self):
        """Check if user has customer role"""
        return self.role == 'Customer'
    
    def has_role(self, role):
        """Check if user has specific role"""
        return self.role == role
    
    def can_access_admin_features(self):
        """Check if user can access admin-only features"""
        return self.is_admin()
    
    def can_manage_inventory(self):
        """Check if user can manage inventory (Admin and Pharmacist)"""
        return self.role in ['Admin', 'Pharmacist']
    
    def can_manage_prescriptions(self):
        """Check if user can manage prescriptions (Admin and Pharmacist)"""
        return self.role in ['Admin', 'Pharmacist']
    
    def can_manage_patients(self):
        """Check if user can manage patients (Admin and Pharmacist)"""
        return self.role in ['Admin', 'Pharmacist']
    
    def can_view_reports(self):
        """Check if user can view reports (Admin and Pharmacist)"""
        return self.role in ['Admin', 'Pharmacist']
    
    def can_manage_users(self):
        """Check if user can manage other users (Admin only)"""
        return self.is_admin()
    
    def can_manage_suppliers(self):
        """Check if user can manage suppliers (Admin and Pharmacist)"""
        return self.role in ['Admin', 'Pharmacist']

class Medicine(db.Model):
    __tablename__ = 'medicines'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    batch_number = db.Column(db.String(50), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    expiry_date = db.Column(db.Date, nullable=False)
    price = db.Column(db.Float, nullable=False)
    gst_percent = db.Column(db.Float, nullable=False)
    
    # Enhanced inventory management fields
    minimum_stock_level = db.Column(db.Integer, default=10, nullable=False)
    maximum_stock_level = db.Column(db.Integer, default=1000, nullable=False)
    location = db.Column(db.String(100), nullable=True)  # Storage location/shelf
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=True)
    unit_of_measurement = db.Column(db.String(20), default='Units', nullable=False)
    manufacturer = db.Column(db.String(100), nullable=True)
    
    # Tracking fields
    reorder_point = db.Column(db.Integer, default=5, nullable=False)
    last_restocked_date = db.Column(db.Date, nullable=True)
    cost_price = db.Column(db.Float, nullable=True)  # Purchase cost
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    supplier = db.relationship('Supplier', backref='medicines')
    alerts = db.relationship('InventoryAlert', back_populates='medicine', cascade='all, delete-orphan')

    @property
    def stock_status(self):
        if self.quantity == 0:
            return 'Out of Stock'
        elif self.quantity <= self.reorder_point:
            return 'Critical'
        elif self.quantity <= self.minimum_stock_level:
            return 'Low'
        elif self.quantity >= self.maximum_stock_level:
            return 'Overstock'
        else:
            return 'Normal'
    
    @property
    def is_expired(self):
        from datetime import date
        return self.expiry_date < date.today()
    
    @property
    def days_to_expiry(self):
        from datetime import date
        return (self.expiry_date - date.today()).days
    
    @property
    def profit_margin(self):
        if self.cost_price:
            return ((self.price - self.cost_price) / self.cost_price) * 100
        return 0

    def __repr__(self):
        return f'<Medicine {self.name}>'

class Customer(db.Model):
    __tablename__ = 'customers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    address = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    sales = db.relationship('Sale', back_populates='customer', lazy=True)

    def __repr__(self):
        return f'<Customer {self.name}>'

class Sale(db.Model):
    __tablename__ = 'sales'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    prescription_id = db.Column(db.Integer, db.ForeignKey('prescriptions.id'), nullable=True)
    total_amount = db.Column(db.Float, nullable=False)
    gst_amount = db.Column(db.Float, nullable=False)
    discount_amount = db.Column(db.Float, default=0.0, nullable=False)
    
    # Payment and billing details
    payment_method = db.Column(db.String(50), default='Cash', nullable=False)  # Cash, Card, UPI, Insurance
    payment_status = db.Column(db.String(20), default='Paid', nullable=False)  # Paid, Pending, Partial
    insurance_claim_amount = db.Column(db.Float, default=0.0, nullable=False)
    patient_copay = db.Column(db.Float, default=0.0, nullable=False)
    
    # Additional information
    sale_type = db.Column(db.String(30), default='Direct Sale', nullable=False)  # Direct Sale, Prescription Sale
    dispensed_by = db.Column(db.String(100), nullable=True)  # Pharmacist who dispensed
    notes = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    customer = db.relationship('Customer', back_populates='sales', lazy=True)
    prescription = db.relationship('Prescription', back_populates='sales', lazy=True)
    items = db.relationship('SaleItem', backref='sale', lazy=True, cascade='all, delete-orphan')

    @property
    def net_amount(self):
        return self.total_amount - self.discount_amount

    @property
    def total_with_gst(self):
        return self.net_amount + self.gst_amount

    def __repr__(self):
        return f'<Sale ID: {self.id}>'

class SaleItem(db.Model):
    __tablename__ = 'sale_items'

    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.id'), nullable=False)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicines.id'), nullable=False)
    prescription_item_id = db.Column(db.Integer, db.ForeignKey('prescription_items.id'), nullable=True)
    quantity = db.Column(db.Integer, nullable=False)
    price_per_unit = db.Column(db.Float, nullable=False)
    discount_percent = db.Column(db.Float, default=0.0, nullable=False)
    
    # Dispensing information
    dispensed_quantity = db.Column(db.Integer, nullable=False)  # May be different from prescribed quantity
    batch_number = db.Column(db.String(50), nullable=True)
    expiry_date = db.Column(db.Date, nullable=True)
    dispensing_instructions = db.Column(db.Text, nullable=True)

    # Relationships
    medicine = db.relationship('Medicine', backref=db.backref('sale_items', lazy=True))
    prescription_item = db.relationship('PrescriptionItem', backref='sale_items', lazy=True)

    @property
    def item_total(self):
        return self.quantity * self.price_per_unit
    
    @property
    def discount_amount(self):
        return (self.item_total * self.discount_percent) / 100
    
    @property
    def net_amount(self):
        return self.item_total - self.discount_amount

    def __repr__(self):
        return f'<SaleItem SaleID: {self.sale_id} MedicineID: {self.medicine_id}>'

class Supplier(db.Model):
    __tablename__ = 'suppliers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    contact_person = db.Column(db.String(100), nullable=True)
    phone_number = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    address = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    purchases = db.relationship('Purchase', backref='supplier', lazy=True)

    def __repr__(self):
        return f'<Supplier {self.name}>'

class Purchase(db.Model):
    __tablename__ = 'purchases'

    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship('PurchaseItem', backref='purchase', lazy=True)

    def __repr__(self):
        return f'<Purchase ID: {self.id}>'

class PurchaseItem(db.Model):
    __tablename__ = 'purchase_items'

    id = db.Column(db.Integer, primary_key=True)
    purchase_id = db.Column(db.Integer, db.ForeignKey('purchases.id'), nullable=False)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicines.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price_per_unit = db.Column(db.Float, nullable=False)
    medicine = db.relationship('Medicine', backref=db.backref('purchase_items', lazy=True))

    def __repr__(self):
        return f'<PurchaseItem PurchaseID: {self.purchase_id} MedicineID: {self.medicine_id}>'

class Patient(db.Model):
    __tablename__ = 'patients'

    id = db.Column(db.Integer, primary_key=True)
    # Personal Information
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    phone_number = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    address = db.Column(db.Text, nullable=True)
    
    # Insurance Information
    insurance_provider = db.Column(db.String(100), nullable=True)
    insurance_policy_number = db.Column(db.String(50), nullable=True)
    insurance_group_number = db.Column(db.String(50), nullable=True)
    insurance_expiry_date = db.Column(db.Date, nullable=True)
    
    # Emergency Contact
    emergency_contact_name = db.Column(db.String(100), nullable=True)
    emergency_contact_relationship = db.Column(db.String(50), nullable=True)
    emergency_contact_phone = db.Column(db.String(20), nullable=True)
    emergency_contact_email = db.Column(db.String(100), nullable=True)
    
    # Medical Information
    blood_group = db.Column(db.String(5), nullable=True)
    allergies = db.Column(db.Text, nullable=True)
    chronic_conditions = db.Column(db.Text, nullable=True)
    current_medications = db.Column(db.Text, nullable=True)
    
    # System fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    medical_history = db.relationship('MedicalHistory', back_populates='patient', lazy=True, cascade='all, delete-orphan')
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def __repr__(self):
        return f'<Patient {self.first_name} {self.last_name}>'

class MedicalHistory(db.Model):
    __tablename__ = 'medical_history'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    
    # Visit Information
    visit_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    chief_complaint = db.Column(db.Text, nullable=True)
    symptoms = db.Column(db.Text, nullable=True)
    diagnosis = db.Column(db.Text, nullable=True)
    treatment = db.Column(db.Text, nullable=True)
    prescription = db.Column(db.Text, nullable=True)
    
    # Vital Signs
    temperature = db.Column(db.Float, nullable=True)  # in Fahrenheit
    blood_pressure_systolic = db.Column(db.Integer, nullable=True)
    blood_pressure_diastolic = db.Column(db.Integer, nullable=True)
    heart_rate = db.Column(db.Integer, nullable=True)  # beats per minute
    weight = db.Column(db.Float, nullable=True)  # in kg
    height = db.Column(db.Float, nullable=True)  # in cm
    
    # Additional Information
    doctor_name = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    follow_up_date = db.Column(db.Date, nullable=True)
    
    # System fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    patient = db.relationship('Patient', back_populates='medical_history')
    
    @property
    def blood_pressure(self):
        if self.blood_pressure_systolic and self.blood_pressure_diastolic:
            return f"{self.blood_pressure_systolic}/{self.blood_pressure_diastolic}"
        return None
    
    def __repr__(self):
        return f'<MedicalHistory Patient: {self.patient_id} Date: {self.visit_date}>'

class MedicalEquipment(db.Model):
    __tablename__ = 'medical_equipment'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    model_number = db.Column(db.String(50), nullable=True)
    serial_number = db.Column(db.String(50), nullable=False, unique=True)
    category = db.Column(db.String(50), nullable=False)
    manufacturer = db.Column(db.String(100), nullable=True)
    
    # Purchase Information
    purchase_date = db.Column(db.Date, nullable=True)
    purchase_price = db.Column(db.Float, nullable=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=True)
    warranty_expiry = db.Column(db.Date, nullable=True)
    
    # Status and Maintenance
    status = db.Column(db.String(20), default='Active', nullable=False)  # Active, Maintenance, Retired, Damaged
    location = db.Column(db.String(100), nullable=True)
    last_maintenance_date = db.Column(db.Date, nullable=True)
    next_maintenance_date = db.Column(db.Date, nullable=True)
    maintenance_frequency_days = db.Column(db.Integer, default=365, nullable=False)
    
    # Usage tracking
    usage_hours = db.Column(db.Float, default=0.0, nullable=False)
    last_used_date = db.Column(db.Date, nullable=True)
    
    # Additional Information
    description = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    supplier = db.relationship('Supplier', backref='equipment')
    alerts = db.relationship('InventoryAlert', back_populates='equipment', cascade='all, delete-orphan')
    
    @property
    def is_warranty_expired(self):
        from datetime import date
        return self.warranty_expiry and self.warranty_expiry < date.today()
    
    @property
    def maintenance_due(self):
        from datetime import date
        return self.next_maintenance_date and self.next_maintenance_date <= date.today()
    
    @property
    def days_to_maintenance(self):
        from datetime import date
        if self.next_maintenance_date:
            return (self.next_maintenance_date - date.today()).days
        return None

    def __repr__(self):
        return f'<MedicalEquipment {self.name}>'

class InventoryAlert(db.Model):
    __tablename__ = 'inventory_alerts'

    id = db.Column(db.Integer, primary_key=True)
    alert_type = db.Column(db.String(50), nullable=False)  # LOW_STOCK, EXPIRED, EXPIRING_SOON, MAINTENANCE_DUE, OUT_OF_STOCK
    message = db.Column(db.Text, nullable=False)
    severity = db.Column(db.String(20), default='Medium', nullable=False)  # Low, Medium, High, Critical
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_acknowledged = db.Column(db.Boolean, default=False, nullable=False)
    
    # References
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicines.id'), nullable=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey('medical_equipment.id'), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    acknowledged_at = db.Column(db.DateTime, nullable=True)
    acknowledged_by = db.Column(db.String(100), nullable=True)
    
    # Relationships
    medicine = db.relationship('Medicine', back_populates='alerts')
    equipment = db.relationship('MedicalEquipment', back_populates='alerts')
    
    @property
    def item_name(self):
        if self.medicine:
            return self.medicine.name
        elif self.equipment:
            return self.equipment.name
        return "Unknown Item"
    
    @property
    def item_type(self):
        if self.medicine:
            return "Medicine"
        elif self.equipment:
            return "Equipment"
        return "Unknown"

    def __repr__(self):
        return f'<InventoryAlert {self.alert_type} - {self.severity}>'

class Prescription(db.Model):
    __tablename__ = 'prescriptions'

    id = db.Column(db.Integer, primary_key=True)
    prescription_number = db.Column(db.String(50), unique=True, nullable=False)
    
    # Patient and Doctor Information
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_name = db.Column(db.String(100), nullable=False)
    doctor_license = db.Column(db.String(50), nullable=True)
    doctor_contact = db.Column(db.String(20), nullable=True)
    clinic_name = db.Column(db.String(100), nullable=True)
    clinic_address = db.Column(db.Text, nullable=True)
    
    # Prescription Details
    diagnosis = db.Column(db.Text, nullable=True)
    symptoms = db.Column(db.Text, nullable=True)
    patient_age = db.Column(db.Integer, nullable=True)
    patient_weight = db.Column(db.Float, nullable=True)
    
    # Prescription Dates
    prescription_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    valid_until = db.Column(db.Date, nullable=True)
    
    # Status and Processing
    status = db.Column(db.String(20), default='Pending', nullable=False)  # Pending, Partially Dispensed, Fully Dispensed, Expired, Cancelled
    priority = db.Column(db.String(20), default='Normal', nullable=False)  # Normal, Urgent, Emergency
    is_emergency = db.Column(db.Boolean, default=False, nullable=False)
    
    # Insurance and Payment
    insurance_provider = db.Column(db.String(100), nullable=True)
    insurance_policy_number = db.Column(db.String(50), nullable=True)
    insurance_approval_number = db.Column(db.String(50), nullable=True)
    
    # Additional Information
    special_instructions = db.Column(db.Text, nullable=True)
    pharmacist_notes = db.Column(db.Text, nullable=True)
    
    # Tracking
    received_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime, nullable=True)
    dispensed_by = db.Column(db.String(100), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patient = db.relationship('Patient', backref='prescriptions', lazy=True)
    items = db.relationship('PrescriptionItem', back_populates='prescription', lazy=True, cascade='all, delete-orphan')
    sales = db.relationship('Sale', back_populates='prescription', lazy=True)

    @property
    def total_medicines_prescribed(self):
        return len(self.items)
    
    @property
    def total_medicines_dispensed(self):
        return sum(1 for item in self.items if item.dispensed_quantity > 0)
    
    @property
    def is_fully_dispensed(self):
        return all(item.dispensed_quantity >= item.prescribed_quantity for item in self.items)
    
    @property
    def is_expired(self):
        from datetime import date
        return self.valid_until and self.valid_until < date.today()
    
    @property
    def estimated_total_amount(self):
        total = 0
        for item in self.items:
            if item.medicine:
                total += item.prescribed_quantity * item.medicine.price
        return total

    def __repr__(self):
        return f'<Prescription {self.prescription_number}>'

class PrescriptionItem(db.Model):
    __tablename__ = 'prescription_items'

    id = db.Column(db.Integer, primary_key=True)
    prescription_id = db.Column(db.Integer, db.ForeignKey('prescriptions.id'), nullable=False)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicines.id'), nullable=True)
    
    # Medicine Information (in case medicine is not in inventory)
    medicine_name = db.Column(db.String(100), nullable=False)
    medicine_strength = db.Column(db.String(50), nullable=True)
    medicine_form = db.Column(db.String(50), nullable=True)  # Tablet, Capsule, Syrup, etc.
    
    # Prescription Details
    prescribed_quantity = db.Column(db.Integer, nullable=False)
    dispensed_quantity = db.Column(db.Integer, default=0, nullable=False)
    unit = db.Column(db.String(20), default='Units', nullable=False)
    
    # Dosage Instructions
    dosage = db.Column(db.String(100), nullable=True)  # e.g., "1 tablet"
    frequency = db.Column(db.String(100), nullable=True)  # e.g., "twice daily"
    duration = db.Column(db.String(100), nullable=True)  # e.g., "for 7 days"
    timing = db.Column(db.String(100), nullable=True)  # e.g., "after meals"
    route = db.Column(db.String(50), nullable=True)  # e.g., "Oral", "Topical"
    
    # Instructions and Notes
    special_instructions = db.Column(db.Text, nullable=True)
    pharmacist_notes = db.Column(db.Text, nullable=True)
    substitution_allowed = db.Column(db.Boolean, default=True, nullable=False)
    
    # Dispensing Status
    status = db.Column(db.String(20), default='Pending', nullable=False)  # Pending, Dispensed, Partially Dispensed, Out of Stock, Substituted
    dispensed_at = db.Column(db.DateTime, nullable=True)
    dispensed_by = db.Column(db.String(100), nullable=True)
    
    # Substitution Information
    substituted_medicine_id = db.Column(db.Integer, db.ForeignKey('medicines.id'), nullable=True)
    substitution_reason = db.Column(db.String(200), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    prescription = db.relationship('Prescription', back_populates='items')
    medicine = db.relationship('Medicine', foreign_keys=[medicine_id], backref='prescription_items')
    substituted_medicine = db.relationship('Medicine', foreign_keys=[substituted_medicine_id])

    @property
    def remaining_quantity(self):
        return max(0, self.prescribed_quantity - self.dispensed_quantity)
    
    @property
    def is_fully_dispensed(self):
        return self.dispensed_quantity >= self.prescribed_quantity
    
    @property
    def dispensing_percentage(self):
        if self.prescribed_quantity == 0:
            return 0
        return (self.dispensed_quantity / self.prescribed_quantity) * 100

    def __repr__(self):
        return f'<PrescriptionItem {self.medicine_name} - {self.prescribed_quantity} {self.unit}>'
