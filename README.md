
# Medical Shop Management System

## Description

The Medical Shop Management System is a Flask-based web application that allows users to manage the inventory, customers, sales, and generate reports for a medical shop. The application supports adding, editing, and deleting medicines, and integrates with a MySQL database using SQLAlchemy ORM for data management.

## Features

- **Inventory Management**: Add, edit, and delete medicines.
- **Sales Management**: Basic page for sales data management.
- **Customer Management**: Manage customer details.
- **Reports**: Generate reports based on sales and inventory.
- **Error Handling**: Logging for server errors and robust error handling.

## Tech Stack

- **Backend**: Flask (Python web framework)
- **Database**: MySQL (via SQLAlchemy ORM) for production or SQLite (via native connection for testing purposes)
- **Frontend**: HTML, Bootstrap for responsive UI
- **Logging**: Logs errors to `error.log`

## Installation

### Prerequisites

1. **Python**: Ensure that you have Python 3.x installed.
2. **MySQL**: Ensure MySQL server is installed and running locally, with a database named `medical_shop_db`.

### Install Dependencies

Clone the repository and install the required Python packages by running the following commands:

```bash
git clone https://github.com/your-username/medical-shop-management.git
cd medical-shop-management
pip install -r requirements.txt
```

If `requirements.txt` doesn't exist, you can manually install dependencies with the following command:

```
pip install Flask Flask-SQLAlchemy mysql-connector-python
```

### Database Setup

1. **Create the Database**:
   You need to have a MySQL database named `medical_shop_db`. You can create it via the MySQL command line or MySQL Workbench.

   create a database:
   ```
   CREATE DATABASE medical_shop_db;
   ```

2. **Run the Application**:
   You can run the application with the following command:

   ```
   python app.py
   ```

   This will start the Flask development server on `http://127.0.0.1:5000/`.