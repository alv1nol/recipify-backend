from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .user import User
from .recipe import Recipe
from .comment import Comment

__all__ = ['db', 'User', 'Recipe', 'Comment']
