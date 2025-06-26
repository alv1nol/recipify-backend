from flask import Flask
from flask_cors import CORS
from server.models import db
from server.config import Config
from server.controllers.routes import init_routes
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
import os
from server.controllers.routes import init_routes


def create_app():
    app = Flask(__name__)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///recipes.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), '..', 'uploads')
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(app)
    migrate = Migrate(app, db)

    init_routes(app) 

    with app.app_context():
        db.create_all()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
