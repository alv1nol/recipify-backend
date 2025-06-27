from . import db
from datetime import datetime

class Like(db.Model):
    __tablename__ = 'like' 

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref='likes')
    recipe = db.relationship('Recipe', backref='likes')
