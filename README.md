
# 🏥 Medical Management System

A comprehensive web-based Medical Management System built with Flask for managing patients, inventory, prescriptions, and sales in medical facilities.

![Flask](https://img.shields.io/badge/Flask-2.3.3-green) ![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0.27-blue) ![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3.3-purple) ![Python](https://img.shields.io/badge/Python-3.8+-yellow)

## ✨ Features

### 🏥 **Patient Management**
- **Patient Registration**: Complete patient profile with demographics, insurance, and emergency contacts
- **Medical History Tracking**: Comprehensive medical records with visit history, conditions, and medications
- **Insurance Management**: Track insurance providers, policy numbers, and coverage details
- **Patient Search & Filtering**: Advanced search capabilities with multiple filters

### 📦 **Inventory Management**
- **Medicine Inventory**: Track medications with batch numbers, expiration dates, and stock levels
- **Medical Equipment**: Manage medical equipment lifecycle, maintenance schedules, and warranties
- **Smart Alerts**: Automated alerts for low stock, expired items, and maintenance due
- **Supplier Integration**: Link inventory items to suppliers for easy reordering

### 💊 **Prescription & Sales Management**
- **Digital Prescriptions**: Create and manage prescriptions with dosage, frequency, and instructions
- **Dispensing Workflow**: Process prescriptions with real-time stock validation
- **Sales Processing**: Complete sales transactions with multiple payment methods
- **Receipt Generation**: Automated billing and receipt generation

### 👥 **Supplier Management**
- **Supplier Database**: Maintain comprehensive supplier contact information
- **Purchase Tracking**: Monitor purchase orders and delivery schedules
- **Performance Analytics**: Track supplier performance and reliability

### 📊 **Reports & Analytics**
- **Sales Reports**: Detailed sales analytics with date ranges and filters
- **Inventory Reports**: Stock levels, turnover rates, and expiry tracking
- **GST Reports**: Tax-compliant reporting for business operations
- **Profit/Loss Analysis**: Financial performance tracking

## 🛠️ Technology Stack

- **Backend**: Python Flask 2.3.3
- **Database**: SQLite with SQLAlchemy ORM 2.0.27
- **Frontend**: HTML5, CSS3, Bootstrap 5.3.3, JavaScript
- **Forms**: Flask-WTF with comprehensive validation
- **Authentication**: Flask-Login with session management
- **Template Engine**: Jinja2 with inheritance
- **Document Generation**: WeasyPrint for PDF reports
- **Data Export**: OpenPyXL for Excel exports

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)
- Virtual environment (recommended)

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/Yaswanth9347/Medical_Management.git
   cd Medical_Management
   ```

2. **Create and activate virtual environment**
   ```bash
   # Linux/macOS
   python3 -m venv venv
   source venv/bin/activate

   # Windows
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables** (optional)
   ```bash
   cp .env.example .env
   # Edit .env file with your configuration
   ```

5. **Initialize the database**
   ```bash
   python app.py
   ```
   The application will automatically create the SQLite database with all required tables.

6. **Access the application**
   Open your browser and navigate to `http://localhost:5000`
   
   **Default Login:**
   - Username: `admin`
   - Password: `admin`

## 📖 Usage Guide

### Getting Started

1. **Initial Setup**
   - Log in with default credentials
   - Set up suppliers for inventory management
   - Add initial medicine and equipment inventory

2. **Patient Registration**
   - Navigate to Patients → Add Patient
   - Fill in complete patient information including insurance details
   - Add medical history and emergency contacts

3. **Prescription Workflow**
   - Create prescriptions for registered patients
   - Add prescribed medicines with dosage and instructions
   - Process dispensing when patients arrive for pickup

4. **Inventory Management**
   - Monitor stock levels through the Inventory Dashboard
   - Set up automatic alerts for low stock and expiry dates
   - Manage equipment maintenance schedules

### Key Workflows

#### Patient Care Workflow
```
Patient Registration → Medical History → Prescription → Dispensing → Follow-up
```

#### Inventory Management Workflow
```
Stock Receipt → Quality Check → Storage → Dispensing → Reorder
```

#### Sales Process
```
Prescription Validation → Stock Check → Dispensing → Payment → Receipt
```

## 🗄️ Database Schema

The system uses SQLite database with the following main entities:

### Core Tables
- **Patient**: Patient demographics, insurance, emergency contacts
- **MedicalHistory**: Medical records, visit history, treatments
- **Medicine**: Drug inventory with batch tracking and expiry
- **MedicalEquipment**: Equipment inventory and maintenance
- **Prescription**: Digital prescriptions with items
- **Sale**: Sales transactions and billing
- **Supplier**: Supplier contact and management

### Relationships
- Patient ↔ MedicalHistory (One-to-Many)
- Patient ↔ Prescription (One-to-Many)
- Prescription ↔ PrescriptionItem (One-to-Many)
- Medicine ↔ PrescriptionItem (One-to-Many)
- Supplier ↔ Medicine (One-to-Many)

## 🔗 API Endpoints

### Patient Management
- `GET /patients` - List all patients with search and filters
- `POST /add_patient` - Create new patient record
- `GET /patient/<id>` - View detailed patient profile
- `PUT /edit_patient/<id>` - Update patient information
- `POST /add_medical_history` - Add medical history entry

### Prescription Management
- `GET /prescriptions` - List prescriptions with status filters
- `POST /add_prescription` - Create new prescription
- `GET /prescription_detail/<id>` - View prescription details
- `POST /dispense_prescription/<id>` - Process prescription dispensing

### Inventory Management
- `GET /inventory` - List medicine inventory with alerts
- `GET /medical_equipment` - List medical equipment
- `GET /inventory_alerts` - View all inventory alerts
- `POST /add_medicine` - Add new medicine to inventory

### Sales & Reports
- `GET /sales` - List sales transactions
- `GET /reports` - Access various system reports
- `GET /profit_loss_report` - Financial performance report

## 🔒 Security Features

- **CSRF Protection**: All forms protected against Cross-Site Request Forgery
- **Input Validation**: Comprehensive server-side validation for all inputs
- **SQL Injection Prevention**: Parameterized queries through SQLAlchemy ORM
- **Session Management**: Secure session handling with Flask-Login
- **Authentication**: Role-based access control (Admin/User)
- **Data Sanitization**: HTML encoding for user-generated content

## 🧪 Testing

Run the application in development mode:
```bash
export FLASK_ENV=development
python app.py
```

For testing with sample data:
```bash
# Add sample data (if implemented)
python -c "from app import create_sample_data; create_sample_data()"
```

## 🚢 Deployment

### Production Deployment with Gunicorn

1. **Install Gunicorn**
   ```bash
   pip install gunicorn
   ```

2. **Run with Gunicorn**
   ```bash
   gunicorn --bind 0.0.0.0:5000 wsgi:app
   ```

### Docker Deployment

1. **Build Docker Image**
   ```bash
   docker build -t medical-management .
   ```

2. **Run Container**
   ```bash
   docker run -p 5000:5000 medical-management
   ```

### Environment Variables

For production deployment, set these environment variables:

```bash
FLASK_ENV=production
SECRET_KEY=your-super-secret-key
DATABASE_URL=your-database-url
MAIL_SERVER=your-mail-server
MAIL_USERNAME=your-email
MAIL_PASSWORD=your-password
```

## 📁 Project Structure

```
Medical_Management/
├── app.py                 # Main Flask application
├── config.py              # Configuration settings
├── wsgi.py               # WSGI entry point
├── models.py             # Database models
├── forms.py              # WTForms definitions
├── requirements.txt      # Python dependencies
├── .env.example          # Environment variables template
├── static/
│   └── css/
│       └── styles.css    # Custom styles
├── templates/
│   ├── base.html         # Base template
│   ├── dashboard.html    # Dashboard
│   ├── patients/         # Patient templates
│   ├── prescriptions/    # Prescription templates
│   ├── inventory/        # Inventory templates
│   └── reports/          # Report templates
├── migrations/           # Database migrations
└── instance/             # Instance-specific files
```

## 🤝 Contributing

1. **Fork the repository**
2. **Create your feature branch**
   ```bash
   git checkout -b feature/AmazingFeature
   ```
3. **Commit your changes**
   ```bash
   git commit -m 'Add some AmazingFeature'
   ```
4. **Push to the branch**
   ```bash
   git push origin feature/AmazingFeature
   ```
5. **Open a Pull Request**

### Contribution Guidelines
- Follow Python PEP 8 style guidelines
- Add tests for new features
- Update documentation as needed
- Ensure all tests pass before submitting PR

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**Yaswanth**
- GitHub: [@Yaswanth9347](https://github.com/Yaswanth9347)
- Email: yaswanth@example.com

## 🙏 Acknowledgments

- **Flask Community** for excellent documentation and ecosystem
- **Bootstrap Team** for responsive UI components
- **SQLAlchemy** for powerful ORM capabilities
- **WeasyPrint** for PDF generation
- **Font Awesome** for icons

## 📞 Support

For support, please:
- Create an issue in the GitHub repository
- Email: yaswanth@example.com
- Check the documentation in the `docs/` folder

## 🗺️ Roadmap

### Upcoming Features
- [ ] Mobile responsive design improvements
- [ ] Advanced reporting dashboard
- [ ] Email notifications for prescriptions
- [ ] Integration with pharmacy systems
- [ ] Multi-location support
- [ ] Advanced user roles and permissions
- [ ] REST API for mobile app integration

---

**⭐ If you find this project helpful, please consider giving it a star!**
