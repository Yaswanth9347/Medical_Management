from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from models import db, Medicine
import logging

# Initialize Flask App
app = Flask(__name__)

# Database configuration for SQLAlchemy (using MySQL)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:@localhost/medical_shop_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Create tables based on models
def create_db():
    with app.app_context():
        db.create_all()

# Route to display all medicines in the inventory using SQLAlchemy
@app.route('/medicines')
def inventory():
    medicines = Medicine.query.all()  
    return render_template('inventory.html', medicines=medicines)

# Route to add a new medicine to the inventory
@app.route('/add_medicine', methods=['GET', 'POST'])
def add_medicine():
    if request.method == 'POST':
        name = request.form['name']
        batch_number = request.form['batch_number']
        expiry_date = request.form['expiry_date']
        quantity = request.form['quantity']
        price = request.form['price']
        category = request.form['category']
        gst_percent = request.form['gst_percent']

        # Create a new Medicine object
        new_medicine = Medicine(
            name=name,
            batch_number=batch_number,
            expiry_date=expiry_date,
            quantity=quantity,
            price=price,
            category=category,
            gst_percent=gst_percent
        )
        db.session.add(new_medicine)
        db.session.commit()
        return redirect(url_for('inventory'))
    return render_template('add_medicine.html')

# Route to edit an existing medicine
@app.route('/edit_medicine/<int:id>', methods=['GET', 'POST'])
def edit_medicine(id):
    medicine = Medicine.query.get(id)
    if request.method == 'POST':
        medicine.name = request.form['name']
        medicine.batch_number = request.form['batch_number']
        medicine.expiry_date = request.form['expiry_date']
        medicine.quantity = request.form['quantity']
        medicine.price = request.form['price']
        medicine.category = request.form['category']
        medicine.gst_percent = request.form['gst_percent']
        
        db.session.commit()
        return redirect(url_for('inventory'))
    return render_template('edit_medicine.html', medicine=medicine)

# Route to delete a medicine
@app.route('/delete_medicine/<int:id>', methods=['GET', 'POST'])
def delete_medicine(id):
    medicine = Medicine.query.get(id)
    db.session.delete(medicine)
    db.session.commit()
    return redirect(url_for('inventory'))

# Route for Sales Management
@app.route('/sales')
def sales():
    return render_template('sales.html')

# Route for Customer Management
@app.route('/customers')
def customers():
    return render_template('customers.html')

# Route for Reports
@app.route('/reports')
def reports():
    return render_template('reports.html')

# Main Dashboard route
@app.route('/')
def dashboard():
    medicine_count = Medicine.query.count()
    return render_template("dashboard.html", medicine_count=medicine_count)

logging.basicConfig(filename='error.log', level=logging.ERROR)

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f'Server Error: {error}')
    return "Something went wrong.", 500

if __name__ == '__main__':
    with app.app_context():
        create_db()
    app.run(debug=True)
