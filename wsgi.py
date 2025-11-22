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
from models import User, db
from alembic import command as alembic_command
from alembic.config import Config as AlembicConfig

# Set production configuration if environment is production
config_name = os.environ.get('FLASK_ENV', 'development')

# Run migrations (optional) and ensure default admin exists
with app.app_context():
    try:
        if os.environ.get('RUN_MIGRATIONS', '1') == '1':
            # Alembic migration upgrade to head
            alembic_ini_path = os.path.join(os.path.dirname(__file__), 'migrations', 'alembic.ini')
            if os.path.exists(alembic_ini_path):
                alembic_cfg = AlembicConfig(alembic_ini_path)
                alembic_command.upgrade(alembic_cfg, 'head')
                print("✅ Alembic migrations applied")
            else:
                print("⚠️ Alembic config not found; skipping migrations")

        # Create default admin (does NOT create tables; assumes migrations applied)
        create_default_admin()
    except Exception as e:
        print(f"❌ Startup initialization error: {e}")

# WSGI application object
application = app

if __name__ == "__main__":
    # For direct execution (not recommended for production)
    port = int(os.environ.get('PORT', 8080))
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