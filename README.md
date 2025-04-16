Medical Shop Management System
A lightweight Medical Shop Management System built using Flask, SQLite, and a clean, modular structure. This system allows users to manage medicines, customers, sales, and reports efficiently through a responsive web interface.

Project Structure
medical_shop_app/
│
├── app.py               # Main Flask application
├── config.py            # DB configuration
├── models.py            # SQLite table setup
├── templates/           # HTML Jinja2 templates
├── static/              # CSS, JS, images
├── tests/               # All unit and integration test files
│   ├── test_medicine.py
│   ├── test_sales.py
│   ├── test_customers.py
│   └── test_reports.py
├── requirements.txt     # Required packages
└── README.md            # Project documentation
⚙️ Requirements
Install the dependencies before running the app:

pip install -r requirements.txt
requirements.txt

flask
pytest
flask_sqlalchemy
🧠 Features
✅ Medicine Inventory Management
Add, edit, and delete medicines

Track quantity, expiry date, and batch

✅ Sales Management
Process sales

Update inventory after each sale

View sales history

✅ Customer Management
Add, edit, and delete customer info

Track their purchase history

✅ Reporting
Generate sales reports by date range

Check inventory status and upcoming expiry

🏗️ Database Setup
Make sure you run the following inside models.py (or through sqlite3 shell or DB browser) to initialize the database:

import sqlite3

conn = sqlite3.connect('medical.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS medicines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    batch TEXT NOT NULL,
    expiry DATE NOT NULL,
    quantity INTEGER NOT NULL,
    price REAL NOT NULL
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    contact TEXT,
    email TEXT
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    medicine_id INTEGER,
    customer_id INTEGER,
    quantity INTEGER,
    total_price REAL,
    date TEXT,
    FOREIGN KEY(medicine_id) REFERENCES medicines(id),
    FOREIGN KEY(customer_id) REFERENCES customers(id)
)
''')

conn.commit()
conn.close()
🚀 Running the Application
Run the Flask application using:

bash
Copy
Edit
python app.py
It will be hosted at: http://127.0.0.1:5000

🧪 Running Tests
To run all unit tests:

pytest tests/

🧰 Debugging Tips
Check logs and traceback in console.

Make sure SQLite tables are created before running the server.

Enable Flask debugger by setting debug=True in app.run().

🌐 Future Improvements
Role-based authentication

PDF/Excel export for reports

Stock threshold alerts

Switch to MySQL via XAMPP for production