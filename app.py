import os
import logging

from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

# Import extensions
from extensions import db, login_manager

# Configure logging
logging.basicConfig(level=logging.DEBUG)

def create_app():
    # Create the app
    app = Flask(__name__)
    app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    # Configure the database
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///visionfit.db")
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'login'

    @login_manager.user_loader
    def load_user(user_id):
        from models import User
        return User.query.get(int(user_id))

    with app.app_context():
        # Import models first
        import models

        # Create all tables
        db.create_all()

    return app

# Create the app instance
app = create_app()

# Import and register routes after app creation
# We need to import routes here to avoid circular imports
import routes

# Register all routes with the Flask app instance
routes.register_routes(app)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
