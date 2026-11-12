import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# The db object holds the application's database connection.
# Models are defined against it.
db = SQLAlchemy()


def create_app(config=None):
    """Application factory: creates a new Flask app on each call.

    This pattern lets tests build the app with different settings,
    such as an in-memory SQLite database.
    """
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL", "sqlite:///dev.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Apply overrides before init_app so they take effect for the database.
    if config:
        app.config.update(config)

    db.init_app(app)

    from app.routes import bp
    app.register_blueprint(bp)

    # Create tables. In a real project, use migrations (Flask-Migrate) instead.
    with app.app_context():
        from app import models  # noqa: F401  (registers the models with db)
        db.create_all()

    return app
