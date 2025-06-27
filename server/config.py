import os
from dotenv import load_dotenv

load_dotenv() 
class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'fallback-secret-key')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///recipes.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-fallback-key')
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1 hour