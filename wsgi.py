"""
WSGI Entry Point for Medical Management System.

This module provides the WSGI application object for production deployment
with servers like Gunicorn, uWSGI, or mod_wsgi.

Usage:
    # Development
    python wsgi.py

    # Production with Gunicorn
    gunicorn --bind 0.0.0.0:5000 wsgi:app
    
    # Production with specific workers
    gunicorn --workers 4 --bind 0.0.0.0:5000 wsgi:app
"""

import os
import sys
from werkzeug.security import generate_password_hash

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

from app import app, create_default_admin
from models import User

# Set production configuration if environment is production
config_name = os.environ.get('FLASK_ENV', 'development')

# Initialize database and create default admin user for production
with app.app_context():
    try:
        # Create all database tables
        from models import db
        db.create_all()
        
        # Create default admin user
        create_default_admin()
            
    except Exception as e:
        print(f"❌ Database initialization error: {e}")

# WSGI application object
application = app

if __name__ == "__main__":
    # For direct execution (not recommended for production)
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = config_name == 'development'
    
    print(f"🚀 Starting Medical Management System")
    print(f"   Environment: {config_name}")
    print(f"   Host: {host}:{port}")
    print(f"   Debug mode: {debug}")
    
    app.run(
        host=host,
        port=port,
        debug=debug
    )