"""Database extension module.

Sets up SQLAlchemy and Flask-Migrate for database operations.
"""

from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
migrate = Migrate()


def init_app(app: Flask) -> None:
    """Initialize the database extension.

    Args:
        app: The Flask application.

    """
    db.init_app(app)
    migrate.init_app(app, db)
