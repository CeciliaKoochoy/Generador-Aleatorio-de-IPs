from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy
from os import path
import sqlite3


db = SQLAlchemy()
DB_NAME = "database.db"


def create_app():
    app = Flask(__name__)
    app.secret_key = 'tu_clave_secreta'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    db.init_app(app)
    
 
    from .views import views
    
    app.register_blueprint(views, url_prefix="/")
    
        
    
    with app.app_context():
        db.create_all()
    
    return app



