from flask import Flask
from flask_cors import CORS
from server.models import db
from server.config import Config
from server.controllers.routes import init_routes
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
import os

jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app, supports_credentials=True, resources={r"/api/*": {"origins": "http://localhost:5173"}})
    jwt.init_app(app)
    db.init_app(app)
    Migrate(app, db)

    init_routes(app)

    with app.app_context():
        db.create_all()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
