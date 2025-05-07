import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

# Set up Base class for models
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy
db = SQLAlchemy(model_class=Base)

def init_db(app):
    """Initialize the database with the given Flask app"""
    # Configure the database
    database_url = os.environ.get("DATABASE_URL")
    # For debugging
    if not database_url:
        logging.warning("DATABASE_URL not found in environment variables! Using SQLite fallback.")
        database_url = "sqlite:///quiz_app.db"

    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    
    # Initialize the app with the extension
    db.init_app(app)
    
    # Create all tables
    with app.app_context():
        from models import User, QuizAttempt, QuizQuestion, Feedback
        db.create_all()
        logging.info("Database tables created!")