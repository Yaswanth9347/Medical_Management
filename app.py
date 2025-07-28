from flask import Flask, render_template, request, redirect, url_for, flash, make_response
from dotenv import load_dotenv
load_dotenv()
from flask_sqlalchemy import SQLAlchemy
from models import db, Medicine, User, Sale, Customer
from forms import MedicineForm, LoginForm, RegistrationForm, SaleForm, CustomerForm
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from weasyprint import HTML
from sqlalchemy import func
from datetime import date
import calendar
import logging
from functools import wraps
import os
import sys
import subprocess
from flask import send_file
from werkzeug.utils import secure_filename

# Initialize Flask App
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

from config import DB_CONFIG

# Database configuration for SQLAlchemy (using MySQL)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Create tables based on models
def create_db():
    with app.app_context():
        db.create_all()

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
def inventory():
    from datetime import date, datetime
    query = request.args.get('query')
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    medicines_query = Medicine.query

    if query:
        medicines_query = medicines_query.filter(Medicine.name.like(f'%{query}%'))

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

    return render_template('inventory.html', medicines=medicines)

# Route to add a new medicine to the inventory
@app.route('/add_medicine', methods=['GET', 'POST'])
@login_required
def add_medicine():
    form = MedicineForm()
    if form.validate_on_submit():
        new_medicine = Medicine(
            name=form.name.data,
            batch_number=form.batch_number.data,
            expiry_date=form.expiry_date.data,
            quantity=form.quantity.data,
            price=form.price.data,
            category=form.category.data,
            gst_percent=form.gst_percent.data
        )
        db.session.add(new_medicine)
        db.session.commit()
        flash('Medicine added successfully!', 'success')
        return redirect(url_for('inventory'))
    return render_template('add_medicine.html', form=form)

# Route to edit an existing medicine
@app.route('/edit_medicine/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_medicine(id):
    medicine = Medicine.query.get_or_404(id)
    form = MedicineForm(obj=medicine)
    if form.validate_on_submit():
        medicine.name = form.name.data
        medicine.batch_number = form.batch_number.data
        medicine.expiry_date = form.expiry_date.data
        medicine.quantity = form.quantity.data
        medicine.price = form.price.data
        medicine.category = form.category.data
        medicine.gst_percent = form.gst_percent.data
        db.session.commit()
        flash('Medicine updated successfully!', 'success')
        return redirect(url_for('inventory'))
    return render_template('edit_medicine.html', form=form, medicine=medicine)

# Route to delete a medicine
@app.route('/delete_medicine/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_medicine(id):
    medicine = Medicine.query.get(id)
    db.session.delete(medicine)
    db.session.commit()
    flash('Medicine deleted successfully!', 'success')
    return redirect(url_for('inventory'))

# Route for Sales Management
@app.route('/sales', methods=['GET', 'POST'])
@login_required
def sales():
    from datetime import datetime
    form = SaleForm()
    form.medicine.choices = [(m.id, m.name) for m in Medicine.query.order_by('name')]
    form.customer.choices = [(c.id, c.name) for c in Customer.query.order_by('name')]

    if form.validate_on_submit():
        medicine = Medicine.query.get(form.medicine.data)
        customer = Customer.query.get(form.customer.data)
        if medicine.quantity >= form.quantity.data:
            total_price = medicine.price * form.quantity.data
            gst_amount = total_price * (medicine.gst_percent / 100)
            
            sale = Sale(
                customer=customer,
                total_amount=total_price,
                gst_amount=gst_amount
            )
            db.session.add(sale)
            
            medicine.quantity -= form.quantity.data
            db.session.commit()
            
            flash('Sale created successfully!', 'success')
            return redirect(url_for('generate_bill', sale_id=sale.id))
        else:
            flash('Not enough stock available.', 'danger')

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
    
    if form.validate_on_submit():
        medicine = Medicine.query.get(form.medicine.data)
        if medicine.quantity >= form.quantity.data:
            total_price = medicine.price * form.quantity.data
            gst_amount = total_price * (medicine.gst_percent / 100)
            
            sale = Sale(
                total_amount=total_price,
                gst_amount=gst_amount
            )
            db.session.add(sale)
            
            medicine.quantity -= form.quantity.data
            db.session.commit()
            
            flash('Sale created successfully!', 'success')
            return redirect(url_for('sales'))
        else:
            flash('Not enough stock available.', 'danger')

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

# Route for Customer Management
@app.route('/customers', methods=['GET', 'POST'])
@login_required
def customers():
    form = CustomerForm()
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
        
    customers = Customer.query.all()
    return render_template('customers.html', form=form, customers=customers)

@app.route('/edit_customer/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_customer(id):
    customer = Customer.query.get_or_404(id)
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
    customer = Customer.query.get(id)
    db.session.delete(customer)
    db.session.commit()
    flash('Customer deleted successfully!', 'success')
    return redirect(url_for('customers'))

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
    sale = Sale.query.get_or_404(sale_id)
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
        db_user = 'yaswanth'
        db_password = 'Amma9347'
        db_name = 'medical_db'
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
            db_user = 'yaswanth'
            db_password = 'Amma9347'
            db_name = 'medical_db'

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
    from datetime import date, datetime
    medicine_count = Medicine.query.count()
    expired_medicines = Medicine.query.filter(Medicine.expiry_date < date.today()).all()
    low_stock_medicines = Medicine.query.filter(Medicine.quantity < 10).all()
    customer_count = Customer.query.count()

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

    return render_template("dashboard.html", medicine_count=medicine_count, expired_medicines=expired_medicines, low_stock_medicines=low_stock_medicines, customer_count=customer_count, total_daily_sales=total_daily_sales, total_monthly_sales=total_monthly_sales, start_date=start_date, end_date=end_date, medicines=medicines)

from flask_mail import Mail, Message
import secrets

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'your_email@gmail.com'  # Replace with your email
app.config['MAIL_PASSWORD'] = 'your_password'  # Replace with your password
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
    form = RegistrationForm()  # Reusing RegistrationForm for username input
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            token = secrets.urlsafe_base64(16)
            user.password_reset_token = token
            db.session.commit()
            msg = Message('Password Reset Request',
                          sender='your_email@gmail.com',  # Replace with your email
                          recipients=[user.username])
            msg.body = f'To reset your password, visit the following link:\n\nhttp://localhost:5000/reset_password/{token}'
            mail.send(msg)
            flash('A password reset link has been sent to your email address.', 'success')
            return redirect(url_for('login'))
        else:
            flash('User not found.', 'danger')
    return render_template('reset_password_request.html', form=form)

# Route for resetting the password
@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.query.filter_by(password_reset_token=token).first()
    if not user:
        flash('Invalid token.', 'danger')
        return redirect(url_for('login'))

    form = RegistrationForm()  # Reusing RegistrationForm for password input
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
        user.password_hash = hashed_password
        user.password_reset_token = None
        db.session.commit()
        flash('Your password has been reset.', 'success')
        return redirect(url_for('login'))

    return render_template('reset_password.html', form=form)

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
    user = User.query.get_or_404(id)
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
    user = User.query.get(id)
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
    port = 5000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    print(f"\n App running at: http://localhost:{port}/\n")
    app.run(debug=True, port=port)
