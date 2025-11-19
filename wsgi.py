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
from app import app
from config import get_config

# Set production configuration if environment is production
if os.environ.get('FLASK_ENV') == 'production':
    config = get_config('production')
    app.config.from_object(config)

# WSGI application object
application = app

if __name__ == "__main__":
    # For direct execution (not recommended for production)
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    print(f"Starting Medical Management System on {host}:{port}")
    print(f"Environment: {os.environ.get('FLASK_ENV', 'development')}")
    print(f"Debug mode: {debug}")
    
    app.run(
        host=host,
        port=port,
        debug=debug
    )