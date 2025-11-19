from flask import Flask, render_template, request, redirect, url_for, flash, make_response, abort
import json
import os
import sys
import subprocess
from datetime import date, datetime
import calendar
import logging
from functools import wraps

from dotenv import load_dotenv
load_dotenv()

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# Optional PDF generation (WeasyPrint may not be available in all deployments)
try:
    from weasyprint import HTML
    PDF_GENERATION_AVAILABLE = True
except ImportError:
    PDF_GENERATION_AVAILABLE = False
    print("Warning: WeasyPrint not available. PDF generation disabled.")

from sqlalchemy import func, or_
from flask import send_file

from config import get_config
from models import db, Medicine, User, Sale, SaleItem, Customer, Supplier, Purchase, Patient, MedicalHistory, MedicalEquipment, InventoryAlert, Prescription, PrescriptionItem
from forms import (
    MedicineForm,
    LoginForm,
    RegistrationForm,
    SaleForm,
    CustomerForm,
    PasswordResetRequestForm,
    PasswordResetForm,
    SupplierForm,
    PurchaseForm,
    PatientForm,
    MedicalHistoryForm,
    MedicalEquipmentForm,
    InventoryAlertForm,
    PrescriptionForm,
    PrescriptionItemForm,
    EnhancedSaleForm,
    DispenseForm,
    AdminUserForm,
    EditUserForm,
)

# Initialize Flask App with proper configuration
def create_app(config_name=None):
    """Application factory pattern."""
    app = Flask(__name__)
    
    # Load configuration
    config = get_config(config_name)
    app.config.from_object(config)
    
    # Initialize extensions
    db.init_app(app)
    
    return app

# Create app instance
app = create_app()

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Role-based authorization decorators
def admin_required(f):
    """Decorator that requires admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        if not current_user.is_admin():
            flash('Admin access required. You do not have permission to access this page.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def pharmacist_required(f):
    """Decorator that requires pharmacist or admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        if not current_user.can_manage_inventory():
            flash('Pharmacist access required. You do not have permission to access this page.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def staff_required(f):
    """Decorator that requires staff access (admin or pharmacist)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        if current_user.is_customer():
            flash('Staff access required. You do not have permission to access this page.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*roles):
    """Decorator that requires one of the specified roles"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('login'))
            if not current_user.role in roles:
                flash(f'Access denied. Required role: {" or ".join(roles)}', 'error')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Initialize database migration
migrate = Migrate(app, db)

# Create tables based on models
def create_db():
    """Create all database tables and default admin user."""
    with app.app_context():
        db.create_all()
        create_default_admin()
        print("Database tables created successfully!")

def create_default_admin():
    """Create default admin user if it doesn't exist."""
    admin_user = User.query.filter_by(username='Admin').first()
    if not admin_user:
        hashed_password = generate_password_hash('Admin@13', method='pbkdf2:sha256')
        admin_user = User(
            username='Admin',
            password_hash=hashed_password,
            role='Admin'
        )
        db.session.add(admin_user)
        db.session.commit()
        print("Default admin user created: Admin / Admin@13")
    else:
        print("Default admin user already exists.")

# Configure logging
def setup_logging():
    """Set up logging configuration."""
    log_level = logging.DEBUG if app.config.get('DEBUG') else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s %(levelname)s %(name)s %(message)s',
        handlers=[
            logging.FileHandler('error.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)

# Profit/Loss Report Route
@app.route('/reports/profit_loss')
@login_required
def profit_loss_report():
    from datetime import date, timedelta
    # Example: Calculate profit/loss for the last 30 days
    today = date.today()
    report_rows = []
    for i in range(30):
        day = today - timedelta(days=i)
        sales = Sale.query.filter(func.date(Sale.created_at) == day).all()
        total_sales = sum(sale.total_amount for sale in sales)
        # For demo, assume purchase cost is 80% of sale (replace with real logic if available)
        total_purchases = total_sales * 0.8
        profit_loss = total_sales - total_purchases
        report_rows.append({
            'date': day.strftime('%Y-%m-%d'),
            'total_sales': total_sales,
            'total_purchases': total_purchases,
            'profit_loss': profit_loss
        })
    report_rows.reverse()
    return render_template('profit_loss_report.html', report_rows=report_rows)

# Route for user registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
        new_user = User(username=form.username.data, password_hash=hashed_password, role=form.role.data)
        db.session.add(new_user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

# Route for user login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember.data)
            return redirect(url_for('dashboard'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html', form=form)


# Route for user logout
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

# Route to display all medicines in the inventory using SQLAlchemy
@app.route('/inventory')
@login_required
@staff_required
def inventory():
    from datetime import date, datetime
    query = request.args.get('query')
    category = request.args.get('category')
    batch_number = request.args.get('batch_number')
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    medicines_query = Medicine.query

    if query:
        medicines_query = medicines_query.filter(Medicine.name.like(f'%{query}%'))
    if category:
        medicines_query = medicines_query.filter(Medicine.category.ilike(f'%{category}%'))
    if batch_number:
        medicines_query = medicines_query.filter(Medicine.batch_number.ilike(f'%{batch_number}%'))

    if start_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        medicines_query = medicines_query.filter(Medicine.expiry_date >= start_date)

    if end_date_str:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        medicines_query = medicines_query.filter(Medicine.expiry_date <= end_date)

    medicines = medicines_query.all()
    
    for medicine in medicines:
        if medicine.quantity == 0:
            medicine.stock_status = 'Out of Stock'
        elif medicine.quantity < 10:
            medicine.stock_status = 'Low'
        else:
            medicine.stock_status = 'In Stock'
        
        if medicine.expiry_date < date.today():
            medicine.is_expired = True
        else:
            medicine.is_expired = False

    return render_template('inventory.html', medicines=medicines, query=query, category=category, batch_number=batch_number)

# Route to add a new medicine to the inventory
@app.route('/add_medicine', methods=['GET', 'POST'])
@login_required
@pharmacist_required
def add_medicine():
    form = MedicineForm()
    if form.validate_on_submit():
        supplier_id = form.supplier_id.data if form.supplier_id.data != 0 else None
        new_medicine = Medicine(
            name=form.name.data,
            batch_number=form.batch_number.data,
            expiry_date=form.expiry_date.data,
            quantity=form.quantity.data,
            price=form.price.data,
            cost_price=form.cost_price.data,
            category=form.category.data,
            gst_percent=form.gst_percent.data,
            minimum_stock_level=form.minimum_stock_level.data,
            maximum_stock_level=form.maximum_stock_level.data,
            reorder_point=form.reorder_point.data,
            location=form.location.data,
            unit_of_measurement=form.unit_of_measurement.data,
            manufacturer=form.manufacturer.data,
            supplier_id=supplier_id,
            last_restocked_date=form.last_restocked_date.data
        )
        db.session.add(new_medicine)
        db.session.commit()
        flash('Medicine added successfully!', 'success')
        return redirect(url_for('inventory'))
    return render_template('add_medicine.html', form=form)

# Route to edit an existing medicine
@app.route('/edit_medicine/<int:id>', methods=['GET', 'POST'])
@login_required
@pharmacist_required
def edit_medicine(id):
    medicine = db.session.get(Medicine, id)
    if not medicine:
        abort(404)
    form = MedicineForm(obj=medicine)
    if form.validate_on_submit():
        supplier_id = form.supplier_id.data if form.supplier_id.data != 0 else None
        medicine.name = form.name.data
        medicine.batch_number = form.batch_number.data
        medicine.expiry_date = form.expiry_date.data
        medicine.quantity = form.quantity.data
        medicine.price = form.price.data
        medicine.cost_price = form.cost_price.data
        medicine.category = form.category.data
        medicine.gst_percent = form.gst_percent.data
        medicine.minimum_stock_level = form.minimum_stock_level.data
        medicine.maximum_stock_level = form.maximum_stock_level.data
        medicine.reorder_point = form.reorder_point.data
        medicine.location = form.location.data
        medicine.unit_of_measurement = form.unit_of_measurement.data
        medicine.manufacturer = form.manufacturer.data
        medicine.supplier_id = supplier_id
        medicine.last_restocked_date = form.last_restocked_date.data
        db.session.commit()
        flash('Medicine updated successfully!', 'success')
        return redirect(url_for('inventory'))
    return render_template('edit_medicine.html', form=form, medicine=medicine)

# Route to delete a medicine
@app.route('/delete_medicine/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_medicine(id):
    medicine = db.session.get(Medicine, id)
    db.session.delete(medicine)
    db.session.commit()
    flash('Medicine deleted successfully!', 'success')
    return redirect(url_for('inventory'))

# Route for Sales Management
@app.route('/sales', methods=['GET', 'POST'])
@login_required
def sales():
    from datetime import datetime
    from models import SaleItem
    form = SaleForm()
    
    # Populate choices for customer and medicine fields
    form.customer.choices = [(c.id, c.name) for c in Customer.query.order_by('name')]
    for item_form in form.items:
        item_form.medicine.choices = [(m.id, m.name) for m in Medicine.query.order_by('name')]

    if form.validate_on_submit():
        customer = db.session.get(Customer, form.customer.data)
        # Create a new sale with customer_id
        
        total_amount = 0
        gst_amount = 0
        
        # Create a new sale
        new_sale = Sale(
            customer_id=customer.id,
            total_amount=0,  # Will be updated after calculating items
            gst_amount=0
        )
        db.session.add(new_sale)
        db.session.flush() # To get the new_sale.id for the SaleItems

        # Process each item in the form
        for item_data in form.items.data:
            medicine = db.session.get(Medicine, item_data['medicine'])
            quantity = item_data['quantity']

            if medicine.quantity < quantity:
                flash(f'Not enough stock for {medicine.name}.', 'danger')
                db.session.rollback()
                return redirect(url_for('sales'))

            price_per_unit = medicine.price
            item_total = price_per_unit * quantity
            item_gst = item_total * (medicine.gst_percent / 100)

            total_amount += item_total
            gst_amount += item_gst

            # Create a new sale item
            sale_item = SaleItem(
                sale_id=new_sale.id,
                medicine_id=medicine.id,
                quantity=quantity,
                price_per_unit=price_per_unit
            )
            db.session.add(sale_item)

            # Update medicine stock
            medicine.quantity -= quantity

        # Update the sale with the final amounts
        new_sale.total_amount = total_amount
        new_sale.gst_amount = gst_amount

        db.session.commit()
        
        flash('Sale created successfully!', 'success')
        return redirect(url_for('generate_bill', sale_id=new_sale.id))

    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    sales_query = Sale.query

    if start_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        sales_query = sales_query.filter(Sale.created_at >= start_date)

    if end_date_str:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        sales_query = sales_query.filter(Sale.created_at <= end_date)

    sales = sales_query.all()
    
    return render_template('sales.html', form=form, sales=sales)

@app.route('/customers', methods=['GET', 'POST'])
@login_required
def customers():
    form = CustomerForm()
    search_query = (request.args.get('search') or '').strip()

    if form.validate_on_submit():
        new_customer = Customer(
            name=form.name.data,
            phone_number=form.phone_number.data,
            email=form.email.data,
            address=form.address.data
        )
        db.session.add(new_customer)
        db.session.commit()
        flash('Customer added successfully!', 'success')
        return redirect(url_for('customers'))

    customers_query = Customer.query
    if search_query:
        like_pattern = f"%{search_query}%"
        customers_query = customers_query.filter(
            or_(
                Customer.name.ilike(like_pattern),
                Customer.phone_number.ilike(like_pattern)
            )
        )

    customers_list = customers_query.order_by(Customer.name).all()
    return render_template(
        'customers.html',
        form=form,
        customers=customers_list,
        search_query=search_query
    )

## (Removed duplicate customers route definition)
@app.route('/customer/<int:customer_id>/history')
@login_required
def customer_history(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    sales = Sale.query.filter_by(customer_id=customer_id).all()
    return render_template('customer_history.html', customer=customer, sales=sales)

@app.route('/edit_customer/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_customer(id):
    customer = db.session.get(Customer, id)
    if not customer:
        abort(404)
    form = CustomerForm(obj=customer)
    if form.validate_on_submit():
        customer.name = form.name.data
        customer.phone_number = form.phone_number.data
        customer.email = form.email.data
        customer.address = form.address.data
        db.session.commit()
        flash('Customer updated successfully!', 'success')
        return redirect(url_for('customers'))
    return render_template('edit_customer.html', form=form, customer=customer)

@app.route('/delete_customer/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_customer(id):
    customer = db.session.get(Customer, id)
    db.session.delete(customer)
    db.session.commit()
    flash('Customer deleted successfully!', 'success')
    return redirect(url_for('customers'))

# Supplier Management Routes
@app.route('/suppliers')
@login_required
def suppliers():
    suppliers = Supplier.query.order_by(Supplier.name).all()
    return render_template('suppliers.html', suppliers=suppliers)

# Medical Equipment Management Routes
@app.route('/medical_equipment')
@login_required
def medical_equipment():
    search_query = (request.args.get('search') or '').strip()
    category_filter = request.args.get('category', '')
    status_filter = request.args.get('status', '')
    
    equipment_query = MedicalEquipment.query
    
    if search_query:
        like_pattern = f"%{search_query}%"
        equipment_query = equipment_query.filter(
            or_(
                MedicalEquipment.name.ilike(like_pattern),
                MedicalEquipment.serial_number.ilike(like_pattern),
                MedicalEquipment.model_number.ilike(like_pattern)
            )
        )
    
    if category_filter:
        equipment_query = equipment_query.filter(MedicalEquipment.category == category_filter)
    
    if status_filter:
        equipment_query = equipment_query.filter(MedicalEquipment.status == status_filter)
    
    equipment_list = equipment_query.order_by(MedicalEquipment.name).all()
    
    # Get unique categories for filter dropdown
    categories = db.session.query(MedicalEquipment.category).distinct().all()
    categories = [cat[0] for cat in categories]
    
    return render_template('medical_equipment.html', 
                         equipment=equipment_list, 
                         search_query=search_query,
                         category_filter=category_filter,
                         status_filter=status_filter,
                         categories=categories)

@app.route('/add_equipment', methods=['GET', 'POST'])
@login_required
def add_equipment():
    form = MedicalEquipmentForm()
    if form.validate_on_submit():
        supplier_id = form.supplier_id.data if form.supplier_id.data != 0 else None
        new_equipment = MedicalEquipment(
            name=form.name.data,
            model_number=form.model_number.data,
            serial_number=form.serial_number.data,
            category=form.category.data,
            manufacturer=form.manufacturer.data,
            purchase_date=form.purchase_date.data,
            purchase_price=form.purchase_price.data,
            supplier_id=supplier_id,
            warranty_expiry=form.warranty_expiry.data,
            status=form.status.data,
            location=form.location.data,
            last_maintenance_date=form.last_maintenance_date.data,
            next_maintenance_date=form.next_maintenance_date.data,
            maintenance_frequency_days=form.maintenance_frequency_days.data,
            usage_hours=form.usage_hours.data,
            last_used_date=form.last_used_date.data,
            description=form.description.data,
            notes=form.notes.data
        )
        db.session.add(new_equipment)
        db.session.commit()
        flash('Medical equipment added successfully!', 'success')
        return redirect(url_for('medical_equipment'))
    return render_template('add_equipment.html', form=form)

@app.route('/edit_equipment/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_equipment(id):
    equipment = db.session.get(MedicalEquipment, id)
    if not equipment:
        abort(404)
    form = MedicalEquipmentForm(obj=equipment)
    if form.validate_on_submit():
        supplier_id = form.supplier_id.data if form.supplier_id.data != 0 else None
        equipment.name = form.name.data
        equipment.model_number = form.model_number.data
        equipment.serial_number = form.serial_number.data
        equipment.category = form.category.data
        equipment.manufacturer = form.manufacturer.data
        equipment.purchase_date = form.purchase_date.data
        equipment.purchase_price = form.purchase_price.data
        equipment.supplier_id = supplier_id
        equipment.warranty_expiry = form.warranty_expiry.data
        equipment.status = form.status.data
        equipment.location = form.location.data
        equipment.last_maintenance_date = form.last_maintenance_date.data
        equipment.next_maintenance_date = form.next_maintenance_date.data
        equipment.maintenance_frequency_days = form.maintenance_frequency_days.data
        equipment.usage_hours = form.usage_hours.data
        equipment.last_used_date = form.last_used_date.data
        equipment.description = form.description.data
        equipment.notes = form.notes.data
        db.session.commit()
        flash('Medical equipment updated successfully!', 'success')
        return redirect(url_for('medical_equipment'))
    return render_template('edit_equipment.html', form=form, equipment=equipment)

@app.route('/delete_equipment/<int:id>', methods=['POST'])
@login_required
def delete_equipment(id):
    equipment = db.session.get(MedicalEquipment, id)
    if not equipment:
        abort(404)
    db.session.delete(equipment)
    db.session.commit()
    flash('Medical equipment deleted successfully!', 'success')
    return redirect(url_for('medical_equipment'))

# Inventory Alerts Management
@app.route('/inventory_alerts')
@login_required
def inventory_alerts():
    # Get filter parameters
    alert_type_filter = request.args.get('alert_type', '')
    severity_filter = request.args.get('severity', '')
    show_acknowledged = request.args.get('show_acknowledged', 'false') == 'true'
    
    alerts_query = InventoryAlert.query
    
    if alert_type_filter:
        alerts_query = alerts_query.filter(InventoryAlert.alert_type == alert_type_filter)
    
    if severity_filter:
        alerts_query = alerts_query.filter(InventoryAlert.severity == severity_filter)
    
    if not show_acknowledged:
        alerts_query = alerts_query.filter(InventoryAlert.is_acknowledged == False)
    
    alerts = alerts_query.filter(InventoryAlert.is_active == True).order_by(
        InventoryAlert.severity.desc(), InventoryAlert.created_at.desc()
    ).all()
    
    return render_template('inventory_alerts.html', 
                         alerts=alerts,
                         alert_type_filter=alert_type_filter,
                         severity_filter=severity_filter,
                         show_acknowledged=show_acknowledged)

@app.route('/acknowledge_alert/<int:alert_id>', methods=['POST'])
@login_required
def acknowledge_alert(alert_id):
    alert = db.session.get(InventoryAlert, alert_id)
    if not alert:
        abort(404)
    
    alert.is_acknowledged = True
    alert.acknowledged_at = datetime.utcnow()
    alert.acknowledged_by = current_user.username
    db.session.commit()
    
    flash('Alert acknowledged successfully!', 'success')
    return redirect(url_for('inventory_alerts'))

@app.route('/dismiss_alert/<int:alert_id>', methods=['POST'])
@login_required
def dismiss_alert(alert_id):
    alert = db.session.get(InventoryAlert, alert_id)
    if not alert:
        abort(404)
    
    alert.is_active = False
    db.session.commit()
    
    flash('Alert dismissed successfully!', 'success')
    return redirect(url_for('inventory_alerts'))

# Enhanced Inventory Dashboard
@app.route('/inventory_dashboard')
@login_required
def inventory_dashboard():
    from datetime import date, timedelta
    
    # Medicine statistics
    total_medicines = Medicine.query.count()
    low_stock_medicines = Medicine.query.filter(Medicine.quantity <= Medicine.reorder_point).count()
    expired_medicines = Medicine.query.filter(Medicine.expiry_date < date.today()).count()
    expiring_soon = Medicine.query.filter(
        Medicine.expiry_date.between(date.today(), date.today() + timedelta(days=30))
    ).count()
    
    # Equipment statistics
    total_equipment = MedicalEquipment.query.count()
    equipment_needing_maintenance = MedicalEquipment.query.filter(
        MedicalEquipment.next_maintenance_date <= date.today()
    ).count()
    active_equipment = MedicalEquipment.query.filter_by(status='Active').count()
    
    # Recent alerts
    recent_alerts = InventoryAlert.query.filter_by(is_active=True, is_acknowledged=False)\
                                       .order_by(InventoryAlert.created_at.desc())\
                                       .limit(10).all()
    
    # Top categories by value
    medicine_categories = db.session.query(
        Medicine.category,
        func.sum(Medicine.quantity * Medicine.price).label('total_value'),
        func.count(Medicine.id).label('item_count')
    ).group_by(Medicine.category).order_by(func.sum(Medicine.quantity * Medicine.price).desc()).limit(10).all()
    
    return render_template('inventory_dashboard.html',
                         total_medicines=total_medicines,
                         low_stock_medicines=low_stock_medicines,
                         expired_medicines=expired_medicines,
                         expiring_soon=expiring_soon,
                         total_equipment=total_equipment,
                         equipment_needing_maintenance=equipment_needing_maintenance,
                         active_equipment=active_equipment,
                         recent_alerts=recent_alerts,
                         medicine_categories=medicine_categories)

# Patient Management Routes
@app.route('/patients')
@login_required
def patients():
    search_query = (request.args.get('search') or '').strip()
    patients_query = Patient.query
    
    if search_query:
        like_pattern = f"%{search_query}%"
        patients_query = patients_query.filter(
            or_(
                Patient.first_name.ilike(like_pattern),
                Patient.last_name.ilike(like_pattern),
                Patient.phone_number.ilike(like_pattern),
                Patient.email.ilike(like_pattern)
            )
        )
    
    patients_list = patients_query.order_by(Patient.first_name, Patient.last_name).all()
    return render_template('patients.html', patients=patients_list, search_query=search_query)

# Prescription Management Routes
@app.route('/prescriptions')
@login_required
def prescriptions():
    search_query = (request.args.get('search') or '').strip()
    status_filter = request.args.get('status', '')
    priority_filter = request.args.get('priority', '')
    
    prescriptions_query = Prescription.query
    
    if search_query:
        like_pattern = f"%{search_query}%"
        prescriptions_query = prescriptions_query.join(Patient).filter(
            or_(
                Prescription.prescription_number.ilike(like_pattern),
                Prescription.doctor_name.ilike(like_pattern),
                Patient.first_name.ilike(like_pattern),
                Patient.last_name.ilike(like_pattern)
            )
        )
    
    if status_filter:
        prescriptions_query = prescriptions_query.filter(Prescription.status == status_filter)
    
    if priority_filter:
        prescriptions_query = prescriptions_query.filter(Prescription.priority == priority_filter)
    
    prescriptions_list = prescriptions_query.order_by(
        Prescription.priority.desc(), 
        Prescription.prescription_date.desc()
    ).all()
    
    return render_template('prescriptions.html', 
                         prescriptions=prescriptions_list,
                         search_query=search_query,
                         status_filter=status_filter,
                         priority_filter=priority_filter)

@app.route('/add_prescription', methods=['GET', 'POST'])
@login_required
def add_prescription():
    form = PrescriptionForm()
    
    # Get all patients and medicines for the form
    patients = Patient.query.all()
    medicines = Medicine.query.filter(Medicine.quantity > 0).all()
    
    # Create JSON data for JavaScript
    patients_json = {}
    for patient in patients:
        patients_json[str(patient.id)] = {
            'first_name': patient.first_name,
            'last_name': patient.last_name,
            'age': patient.age,
            'gender': patient.gender,
            'phone': patient.phone,
            'blood_group': patient.blood_group,
            'allergies': patient.allergies
        }
    
    if form.validate_on_submit():
        new_prescription = Prescription(
            prescription_number=form.prescription_number.data,
            patient_id=form.patient_id.data,
            doctor_name=form.doctor_name.data,
            doctor_license=form.doctor_license.data,
            doctor_contact=form.doctor_contact.data,
            clinic_name=form.clinic_name.data,
            clinic_address=form.clinic_address.data,
            diagnosis=form.diagnosis.data,
            symptoms=form.symptoms.data,
            patient_age=form.patient_age.data,
            patient_weight=form.patient_weight.data,
            prescription_date=form.prescription_date.data,
            valid_until=form.valid_until.data,
            priority=form.priority.data,
            is_emergency=form.is_emergency.data,
            insurance_provider=form.insurance_provider.data,
            insurance_policy_number=form.insurance_policy_number.data,
            insurance_approval_number=form.insurance_approval_number.data,
            special_instructions=form.special_instructions.data,
            pharmacist_notes=form.pharmacist_notes.data
        )
        db.session.add(new_prescription)
        db.session.commit()
        flash('Prescription added successfully!', 'success')
        return redirect(url_for('prescription_detail', prescription_id=new_prescription.id))
    
    return render_template('add_prescription.html', 
                         form=form, 
                         patients=patients,
                         medicines=medicines,
                         patients_json=json.dumps(patients_json))

@app.route('/prescription/<int:prescription_id>')
@login_required
def prescription_detail(prescription_id):
    prescription = Prescription.query.get_or_404(prescription_id)
    return render_template('prescription_detail.html', prescription=prescription)

@app.route('/prescription/<int:prescription_id>/add_item', methods=['GET', 'POST'])
@login_required
def add_prescription_item(prescription_id):
    prescription = Prescription.query.get_or_404(prescription_id)
    form = PrescriptionItemForm()
    
    if form.validate_on_submit():
        medicine_id = form.medicine_id.data if form.medicine_id.data != 0 else None
        new_item = PrescriptionItem(
            prescription_id=prescription_id,
            medicine_id=medicine_id,
            medicine_name=form.medicine_name.data,
            medicine_strength=form.medicine_strength.data,
            medicine_form=form.medicine_form.data,
            prescribed_quantity=form.prescribed_quantity.data,
            unit=form.unit.data,
            dosage=form.dosage.data,
            frequency=form.frequency.data,
            duration=form.duration.data,
            timing=form.timing.data,
            route=form.route.data,
            special_instructions=form.special_instructions.data,
            substitution_allowed=form.substitution_allowed.data
        )
        db.session.add(new_item)
        db.session.commit()
        flash('Medicine added to prescription successfully!', 'success')
        return redirect(url_for('prescription_detail', prescription_id=prescription_id))
    
    return render_template('add_prescription_item.html', form=form, prescription=prescription)

@app.route('/prescription/<int:prescription_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_prescription(prescription_id):
    prescription = Prescription.query.get_or_404(prescription_id)
    form = PrescriptionForm(obj=prescription)
    
    if form.validate_on_submit():
        prescription.prescription_number = form.prescription_number.data
        prescription.patient_id = form.patient_id.data
        prescription.doctor_name = form.doctor_name.data
        prescription.doctor_license = form.doctor_license.data
        prescription.doctor_contact = form.doctor_contact.data
        prescription.clinic_name = form.clinic_name.data
        prescription.clinic_address = form.clinic_address.data
        prescription.diagnosis = form.diagnosis.data
        prescription.symptoms = form.symptoms.data
        prescription.patient_age = form.patient_age.data
        prescription.patient_weight = form.patient_weight.data
        prescription.prescription_date = form.prescription_date.data
        prescription.valid_until = form.valid_until.data
        prescription.priority = form.priority.data
        prescription.is_emergency = form.is_emergency.data
        prescription.insurance_provider = form.insurance_provider.data
        prescription.insurance_policy_number = form.insurance_policy_number.data
        prescription.insurance_approval_number = form.insurance_approval_number.data
        prescription.special_instructions = form.special_instructions.data
        prescription.pharmacist_notes = form.pharmacist_notes.data
        db.session.commit()
        flash('Prescription updated successfully!', 'success')
        return redirect(url_for('prescription_detail', prescription_id=prescription_id))
    
    return render_template('edit_prescription.html', form=form, prescription=prescription)

@app.route('/prescription/<int:prescription_id>/dispense', methods=['GET', 'POST'])
@login_required
def dispense_prescription(prescription_id):
    prescription = Prescription.query.get_or_404(prescription_id)
    
    if request.method == 'POST':
        # Process dispensing
        customer_id = request.form.get('customer_id')
        payment_method = request.form.get('payment_method', 'Cash')
        discount_amount = float(request.form.get('discount_amount', 0))
        insurance_claim_amount = float(request.form.get('insurance_claim_amount', 0))
        dispensed_by = request.form.get('dispensed_by', current_user.username)
        dispensing_notes = request.form.get('dispensing_notes', '')
        
        # Calculate totals
        total_amount = 0
        gst_amount = 0
        
        # Create sale
        sale = Sale(
            customer_id=customer_id,
            prescription_id=prescription_id,
            total_amount=0,  # Will be updated
            gst_amount=0,
            discount_amount=discount_amount,
            payment_method=payment_method,
            payment_status='Paid',
            insurance_claim_amount=insurance_claim_amount,
            sale_type='Prescription Sale',
            dispensed_by=dispensed_by,
            notes=dispensing_notes
        )
        db.session.add(sale)
        db.session.flush()
        
        # Process each prescription item
        for item in prescription.items:
            medicine = item.medicine
            if medicine and medicine.quantity > 0:
                # Get dispensed quantity from form
                dispensed_qty = int(request.form.get(f'dispensed_qty_{item.id}', 0))
                
                if dispensed_qty > 0:
                    # Create sale item
                    sale_item = SaleItem(
                        sale_id=sale.id,
                        medicine_id=medicine.id,
                        prescription_item_id=item.id,
                        quantity=dispensed_qty,
                        dispensed_quantity=dispensed_qty,
                        price_per_unit=medicine.price,
                        batch_number=medicine.batch_number,
                        expiry_date=medicine.expiry_date,
                        dispensing_instructions=f"{item.dosage} {item.frequency} {item.duration}"
                    )
                    db.session.add(sale_item)
                    
                    # Update medicine stock
                    medicine.quantity -= dispensed_qty
                    
                    # Update prescription item
                    item.dispensed_quantity += dispensed_qty
                    item.status = 'Fully Dispensed' if item.is_fully_dispensed else 'Partially Dispensed'
                    item.dispensed_at = datetime.utcnow()
                    item.dispensed_by = dispensed_by
                    
                    # Calculate amounts
                    item_total = dispensed_qty * medicine.price
                    item_gst = item_total * (medicine.gst_percent / 100)
                    
                    total_amount += item_total
                    gst_amount += item_gst
        
        # Update sale totals
        sale.total_amount = total_amount
        sale.gst_amount = gst_amount
        
        # Update prescription status
        if prescription.is_fully_dispensed:
            prescription.status = 'Fully Dispensed'
        else:
            prescription.status = 'Partially Dispensed'
        prescription.processed_at = datetime.utcnow()
        prescription.dispensed_by = dispensed_by
        
        db.session.commit()
        flash('Prescription dispensed successfully!', 'success')
        return redirect(url_for('generate_bill', sale_id=sale.id))
    
    # GET request - show dispensing form
    from models import Customer
    customers = Customer.query.order_by('name').all()
    return render_template('dispense_prescription.html', prescription=prescription, customers=customers)

@app.route('/prescription/<int:prescription_id>/delete', methods=['POST'])
@login_required
def delete_prescription(prescription_id):
    prescription = Prescription.query.get_or_404(prescription_id)
    if prescription.status != 'Pending':
        flash('Cannot delete a prescription that has been processed.', 'error')
        return redirect(url_for('prescriptions'))
    
    db.session.delete(prescription)
    db.session.commit()
    flash('Prescription deleted successfully!', 'success')
    return redirect(url_for('prescriptions'))

@app.route('/add_patient', methods=['GET', 'POST'])
@login_required
def add_patient():
    form = PatientForm()
    if form.validate_on_submit():
        new_patient = Patient(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            date_of_birth=form.date_of_birth.data,
            gender=form.gender.data,
            phone_number=form.phone_number.data,
            email=form.email.data,
            address=form.address.data,
            insurance_provider=form.insurance_provider.data,
            insurance_policy_number=form.insurance_policy_number.data,
            insurance_group_number=form.insurance_group_number.data,
            insurance_expiry_date=form.insurance_expiry_date.data,
            emergency_contact_name=form.emergency_contact_name.data,
            emergency_contact_relationship=form.emergency_contact_relationship.data,
            emergency_contact_phone=form.emergency_contact_phone.data,
            emergency_contact_email=form.emergency_contact_email.data,
            blood_group=form.blood_group.data,
            allergies=form.allergies.data,
            chronic_conditions=form.chronic_conditions.data,
            current_medications=form.current_medications.data
        )
        db.session.add(new_patient)
        db.session.commit()
        flash('Patient added successfully!', 'success')
        return redirect(url_for('patients'))
    return render_template('add_patient.html', form=form)

@app.route('/edit_patient/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_patient(id):
    patient = db.session.get(Patient, id)
    if not patient:
        abort(404)
    form = PatientForm(obj=patient)
    if form.validate_on_submit():
        patient.first_name = form.first_name.data
        patient.last_name = form.last_name.data
        patient.date_of_birth = form.date_of_birth.data
        patient.gender = form.gender.data
        patient.phone_number = form.phone_number.data
        patient.email = form.email.data
        patient.address = form.address.data
        patient.insurance_provider = form.insurance_provider.data
        patient.insurance_policy_number = form.insurance_policy_number.data
        patient.insurance_group_number = form.insurance_group_number.data
        patient.insurance_expiry_date = form.insurance_expiry_date.data
        patient.emergency_contact_name = form.emergency_contact_name.data
        patient.emergency_contact_relationship = form.emergency_contact_relationship.data
        patient.emergency_contact_phone = form.emergency_contact_phone.data
        patient.emergency_contact_email = form.emergency_contact_email.data
        patient.blood_group = form.blood_group.data
        patient.allergies = form.allergies.data
        patient.chronic_conditions = form.chronic_conditions.data
        patient.current_medications = form.current_medications.data
        db.session.commit()
        flash('Patient updated successfully!', 'success')
        return redirect(url_for('patients'))
    return render_template('edit_patient.html', form=form, patient=patient)

@app.route('/delete_patient/<int:id>', methods=['POST'])
@login_required
def delete_patient(id):
    patient = db.session.get(Patient, id)
    if not patient:
        abort(404)
    db.session.delete(patient)
    db.session.commit()
    flash('Patient deleted successfully!', 'success')
    return redirect(url_for('patients'))

@app.route('/patient/<int:patient_id>/profile')
@login_required
def patient_profile(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    medical_history = MedicalHistory.query.filter_by(patient_id=patient_id).order_by(MedicalHistory.visit_date.desc()).all()
    return render_template('patient_profile.html', patient=patient, medical_history=medical_history)

@app.route('/patient/<int:patient_id>/add_medical_history', methods=['GET', 'POST'])
@login_required
def add_medical_history(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    form = MedicalHistoryForm()
    if form.validate_on_submit():
        new_history = MedicalHistory(
            patient_id=patient_id,
            visit_date=form.visit_date.data,
            chief_complaint=form.chief_complaint.data,
            symptoms=form.symptoms.data,
            diagnosis=form.diagnosis.data,
            treatment=form.treatment.data,
            prescription=form.prescription.data,
            temperature=form.temperature.data,
            blood_pressure_systolic=form.blood_pressure_systolic.data,
            blood_pressure_diastolic=form.blood_pressure_diastolic.data,
            heart_rate=form.heart_rate.data,
            weight=form.weight.data,
            height=form.height.data,
            doctor_name=form.doctor_name.data,
            notes=form.notes.data,
            follow_up_date=form.follow_up_date.data
        )
        db.session.add(new_history)
        db.session.commit()
        flash('Medical history added successfully!', 'success')
        return redirect(url_for('patient_profile', patient_id=patient_id))
    return render_template('add_medical_history.html', form=form, patient=patient)

@app.route('/patient/<int:patient_id>/medical_history/<int:history_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_medical_history(patient_id, history_id):
    patient = Patient.query.get_or_404(patient_id)
    history = MedicalHistory.query.get_or_404(history_id)
    if history.patient_id != patient_id:
        abort(403)
    form = MedicalHistoryForm(obj=history)
    if form.validate_on_submit():
        history.visit_date = form.visit_date.data
        history.chief_complaint = form.chief_complaint.data
        history.symptoms = form.symptoms.data
        history.diagnosis = form.diagnosis.data
        history.treatment = form.treatment.data
        history.prescription = form.prescription.data
        history.temperature = form.temperature.data
        history.blood_pressure_systolic = form.blood_pressure_systolic.data
        history.blood_pressure_diastolic = form.blood_pressure_diastolic.data
        history.heart_rate = form.heart_rate.data
        history.weight = form.weight.data
        history.height = form.height.data
        history.doctor_name = form.doctor_name.data
        history.notes = form.notes.data
        history.follow_up_date = form.follow_up_date.data
        db.session.commit()
        flash('Medical history updated successfully!', 'success')
        return redirect(url_for('patient_profile', patient_id=patient_id))
    return render_template('edit_medical_history.html', form=form, patient=patient, history=history)

@app.route('/patient/<int:patient_id>/medical_history/<int:history_id>/delete', methods=['POST'])
@login_required
def delete_medical_history(patient_id, history_id):
    patient = Patient.query.get_or_404(patient_id)
    history = MedicalHistory.query.get_or_404(history_id)
    if history.patient_id != patient_id:
        abort(403)
    db.session.delete(history)
    db.session.commit()
    flash('Medical history deleted successfully!', 'success')
    return redirect(url_for('patient_profile', patient_id=patient_id))

@app.route('/add_supplier', methods=['GET', 'POST'])
@login_required
def add_supplier():
    form = SupplierForm()
    if form.validate_on_submit():
        new_supplier = Supplier(
            name=form.name.data,
            contact_person=form.contact_person.data,
            phone_number=form.phone_number.data,
            email=form.email.data,
            address=form.address.data
        )
        db.session.add(new_supplier)
        db.session.commit()
        flash('Supplier added successfully!', 'success')
        return redirect(url_for('suppliers'))
    return render_template('add_supplier.html', form=form)

@app.route('/edit_supplier/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_supplier(id):
    supplier = db.session.get(Supplier, id)
    if not supplier:
        abort(404)
    form = SupplierForm(obj=supplier)
    if form.validate_on_submit():
        supplier.name = form.name.data
        supplier.contact_person = form.contact_person.data
        supplier.phone_number = form.phone_number.data
        supplier.email = form.email.data
        supplier.address = form.address.data
        db.session.commit()
        flash('Supplier updated successfully!', 'success')
        return redirect(url_for('suppliers'))
    return render_template('edit_supplier.html', form=form, supplier=supplier)

@app.route('/delete_supplier/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_supplier(id):
    supplier = db.session.get(Supplier, id)
    db.session.delete(supplier)
    db.session.commit()
    flash('Supplier deleted successfully!', 'success')
    return redirect(url_for('suppliers'))

# Route for Reports
# Purchase Management Routes
@app.route('/purchases', methods=['GET', 'POST'])
@login_required
def purchases():
    from models import Purchase, PurchaseItem
    form = PurchaseForm()
    
    # Populate choices for supplier and medicine fields
    form.supplier.choices = [(s.id, s.name) for s in Supplier.query.order_by('name')]
    for item_form in form.items:
        item_form.medicine.choices = [(m.id, m.name) for m in Medicine.query.order_by('name')]

    if form.validate_on_submit():
        supplier = Supplier.query.get(form.supplier.data)
        
        total_amount = 0
        
        # Create a new purchase
        new_purchase = Purchase(
            supplier=supplier,
            total_amount=0  # Will be updated after calculating items
        )
        db.session.add(new_purchase)
        db.session.flush()  # To get the new_purchase.id for the PurchaseItems

        # Process each item in the form
        for item_data in form.items.data:
            medicine = Medicine.query.get(item_data['medicine'])
            quantity = item_data['quantity']
            price_per_unit = item_data['price_per_unit']

            item_total = price_per_unit * quantity
            total_amount += item_total

            # Create a new purchase item
            purchase_item = PurchaseItem(
                purchase_id=new_purchase.id,
                medicine_id=medicine.id,
                quantity=quantity,
                price_per_unit=price_per_unit
            )
            db.session.add(purchase_item)

            # Update medicine stock
            medicine.quantity += quantity

        # Update the purchase with the final amount
        new_purchase.total_amount = total_amount
        db.session.commit()
        
        flash('Purchase recorded successfully!', 'success')
        return redirect(url_for('purchases'))

    # Get filter parameters
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    supplier_id = request.args.get('supplier_id')

    purchases_query = Purchase.query

    if start_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        purchases_query = purchases_query.filter(Purchase.created_at >= start_date)

    if end_date_str:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        purchases_query = purchases_query.filter(Purchase.created_at <= end_date)

    if supplier_id:
        purchases_query = purchases_query.filter_by(supplier_id=supplier_id)

    purchases = purchases_query.all()
    
    return render_template('purchases.html', form=form, purchases=purchases)

@app.route('/purchases/<int:purchase_id>')
@login_required
def view_purchase(purchase_id):
    purchase = db.session.get(Purchase, purchase_id)
    if not purchase:
        abort(404)
    return render_template('view_purchase.html', purchase=purchase)

@app.route('/delete_purchase/<int:id>', methods=['POST'])
@login_required
def delete_purchase(id):
    purchase = db.session.get(Purchase, id)
    if not purchase:
        abort(404)
        
    # Restore medicine quantities
    for item in purchase.items:
        medicine = Medicine.query.get(item.medicine_id)
        medicine.quantity -= item.quantity
    
    db.session.delete(purchase)
    db.session.commit()
    flash('Purchase deleted successfully!', 'success')
    return redirect(url_for('purchases'))

# Route for Reports
@app.route('/reports')
@login_required
def reports():
    from datetime import date
    sales = Sale.query.all()
    expired_medicines = Medicine.query.filter(Medicine.expiry_date < date.today()).all()
    inventory = Medicine.query.all()
    return render_template('reports.html', sales=sales, expired_medicines=expired_medicines, inventory=inventory)

@app.route('/sales/<int:sale_id>/bill')
@login_required
def generate_bill(sale_id):
    sale = db.session.get(Sale, sale_id)
    if not sale:
        abort(404)
    
    if not PDF_GENERATION_AVAILABLE:
        flash('PDF generation is not available in this deployment.', 'warning')
        return redirect(url_for('view_sale', sale_id=sale_id))
        
    html = render_template('reports/sale_bill.html', sale=sale)
    
    pdf = HTML(string=html).write_pdf()
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=sale_{sale_id}_bill.pdf'
    return response

@app.route('/download_report/<report_type>')
@login_required
def download_report(report_type):
    from io import BytesIO
    from openpyxl import Workbook
    from datetime import date
    
    # Create Excel workbook
    wb = Workbook()
    ws = wb.active
    
    if report_type == 'sales':
        sales = Sale.query.all()
        ws.append(['Sale ID', 'Date', 'Customer', 'Total Amount', 'GST Amount'])
        for sale in sales:
            ws.append([
                sale.id,
                sale.created_at.strftime('%Y-%m-%d'),
                sale.customer.name if sale.customer else 'N/A',
                sale.total_amount,
                sale.gst_amount
            ])
        
    elif report_type == 'expiry':
        expired_medicines = Medicine.query.filter(Medicine.expiry_date < date.today()).all()
        ws.append(['Medicine', 'Batch', 'Expiry Date', 'Quantity', 'Price'])
        for med in expired_medicines:
            ws.append([med.name, med.batch_number, med.expiry_date, med.quantity, med.price])
            
    elif report_type == 'inventory':
        inventory = Medicine.query.all()
        ws.append(['Medicine', 'Batch', 'Expiry Date', 'Quantity', 'Price'])
        for med in inventory:
            ws.append([med.name, med.batch_number, med.expiry_date, med.quantity, med.price])
            
    elif report_type == 'gst':
        sales = Sale.query.all()
        ws.append(['Sale ID', 'Date', 'GST Percentage', 'GST Amount', 'Total Amount'])
        for sale in sales:
            ws.append([
                sale.id,
                sale.created_at.strftime('%Y-%m-%d'),
                sale.items[0].medicine.gst_percent if sale.items else 'N/A',
                sale.gst_amount,
                sale.total_amount
            ])
    else:
        return "Invalid report type", 400

    # Save Excel to bytes buffer
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    response.headers['Content-Disposition'] = f'attachment; filename={report_type}_report.xlsx'
    return response

@app.route('/backup')
@login_required
def backup():
    try:
        # Replace with your actual database credentials and name
        db_user = os.getenv('DB_USER')
        db_password = os.getenv('DB_PASSWORD')
        db_name = os.getenv('DB_NAME')
        backup_file = 'backup.sql'

        command = f"mysqldump -u {db_user} -p{db_password} {db_name} > {backup_file}"
        subprocess.run(command, shell=True, check=True)

        return send_file(backup_file, as_attachment=True)
    except Exception as e:
        flash(f"Error creating backup: {e}", "danger")
        return redirect(url_for('dashboard'))

@app.route('/restore', methods=['POST'])
@login_required
def restore():
    if 'backup_file' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for('dashboard'))
    file = request.files['backup_file']
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(url_for('dashboard'))
    if file:
        try:
            filename = secure_filename(file.filename)
            filepath = os.path.join('/tmp', filename)
            file.save(filepath)

            # Replace with your actual database credentials and name
            db_user = os.getenv('DB_USER')
            db_password = os.getenv('DB_PASSWORD')
            db_name = os.getenv('DB_NAME')

            command = f"mysql -u {db_user} -p{db_password} {db_name} < {filepath}"
            subprocess.run(command, shell=True, check=True)

            flash('Database restored successfully!', 'success')
        except Exception as e:
            flash(f"Error restoring database: {e}", "danger")
        finally:
            if os.path.exists(filepath):
                os.remove(filepath)
        return redirect(url_for('dashboard'))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.role == 'Admin':
            abort(403)  # Forbidden
        return f(*args, **kwargs)
    return decorated_function


# Main Dashboard route
@app.route('/')
@login_required
def dashboard():
    from datetime import date, datetime, timedelta
    
    # Medicine statistics
    medicine_count = Medicine.query.count()
    expired_medicines = Medicine.query.filter(Medicine.expiry_date < date.today()).all()
    low_stock_medicines = Medicine.query.filter(Medicine.quantity <= Medicine.reorder_point).all()
    customer_count = Customer.query.count()
    
    # Equipment statistics  
    equipment_count = MedicalEquipment.query.count()
    equipment_needing_maintenance = MedicalEquipment.query.filter(
        MedicalEquipment.next_maintenance_date <= date.today()
    ).count()
    
    # Patient statistics
    patient_count = Patient.query.count()
    
    # Recent alerts
    recent_alerts = InventoryAlert.query.filter_by(is_active=True, is_acknowledged=False)\
                                       .order_by(InventoryAlert.created_at.desc())\
                                       .limit(5).all()

    # Calculate daily sales summary
    today = date.today()
    daily_sales = Sale.query.filter(func.date(Sale.created_at) == today).all()
    total_daily_sales = sum(sale.total_amount for sale in daily_sales)

    # Calculate monthly sales summary
    first_day_of_month = datetime(today.year, today.month, 1)
    last_day_of_month = datetime(today.year, today.month, calendar.monthrange(today.year, today.month)[1])
    monthly_sales = Sale.query.filter(Sale.created_at >= first_day_of_month, Sale.created_at <= last_day_of_month).all()
    total_monthly_sales = sum(sale.total_amount for sale in monthly_sales)

    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    if start_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    else:
        start_date = None

    if end_date_str:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    else:
        end_date = None

    medicines_query = Medicine.query

    if start_date:
        medicines_query = medicines_query.filter(Medicine.expiry_date >= start_date)

    if end_date:
        medicines_query = medicines_query.filter(Medicine.expiry_date <= end_date)

    medicines = medicines_query.all()

    # Prepare sales data for the last 7 days for the dashboard graph
    sales_labels = []
    sales_data = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        sales_labels.append(day.strftime('%a'))
        day_sales = Sale.query.filter(func.date(Sale.created_at) == day).all()
        sales_data.append(sum(sale.total_amount for sale in day_sales))

    return render_template(
        "dashboard.html",
        medicine_count=medicine_count,
        expired_medicines=expired_medicines,
        low_stock_medicines=low_stock_medicines,
        customer_count=customer_count,
        equipment_count=equipment_count,
        equipment_needing_maintenance=equipment_needing_maintenance,
        patient_count=patient_count,
        recent_alerts=recent_alerts,
        total_daily_sales=total_daily_sales,
        total_monthly_sales=total_monthly_sales,
        start_date=start_date,
        end_date=end_date,
        medicines=medicines,
        sales_labels=sales_labels,
        sales_data=sales_data
    )

from flask_mail import Mail, Message
import secrets

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
mail = Mail(app)

# Route for listing users (Admin only)
@app.route('/admin/users')
@login_required
@admin_required
def list_users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

# Route for requesting a password reset
@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password_request():
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            token = secrets.token_urlsafe(32)
            user.password_reset_token = token
            db.session.commit()
            msg = Message('Password Reset Request',
                          sender=os.getenv('MAIL_USERNAME'),
                          recipients=[user.username])
            msg.body = f'''To reset your password, visit the following link:
{url_for('reset_password', token=token, _external=True)}

If you did not make this request then simply ignore this email and no changes will be made.
'''
            mail.send(msg)
            flash('An email with instructions to reset your password has been sent.', 'info')
            return redirect(url_for('login'))
    return render_template('reset_password_request.html', title='Reset Password', form=form)

# Route for resetting the password
@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.query.filter_by(password_reset_token=token).first_or_404()
    form = PasswordResetForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
        user.password_hash = hashed_password
        user.password_reset_token = None
        db.session.commit()
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('reset_password.html', title='Reset Password', form=form)

# Route for adding a new user (Admin only)
@app.route('/admin/users/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_user():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
        new_user = User(username=form.username.data, password_hash=hashed_password, role=form.role.data)
        db.session.add(new_user)
        db.session.commit()
        flash('User added successfully!', 'success')
        return redirect(url_for('list_users'))
    return render_template('admin/add_user.html', form=form)

# Route for editing a user (Admin only)
@app.route('/admin/users/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(id):
    user = db.session.get(User, id)
    if not user:
        abort(404)
    form = RegistrationForm(obj=user)
    if form.validate_on_submit():
        user.username = form.username.data
        user.role = form.role.data
        # Password update logic can be added here if needed
        db.session.commit()
        flash('User updated successfully!', 'success')
        return redirect(url_for('list_users'))
    return render_template('admin/edit_user.html', form=form, user=user)

# Route for deleting a user (Admin only)
@app.route('/admin/users/delete/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def delete_user(id):
    user = db.session.get(User, id)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully!', 'success')
    return redirect(url_for('list_users'))

logging.basicConfig(filename='error.log', level=logging.ERROR)

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f'Server Error: {error}')
    return "Something went wrong.", 500

if __name__ == '__main__':
    with app.app_context():
        create_db()
    
    # Railway deployment configuration - MUST use Railway's PORT
    port = int(os.environ.get("PORT", 8080))
    print(f"\n🚀 App starting on port: {port}\n")
    app.run(host="0.0.0.0", port=port, debug=False)
