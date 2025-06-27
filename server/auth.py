from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import check_password_hash
from server.models import db, User

def register_user(username, email, password):
    if User.query.filter_by(username=username).first():
        return {"error": "Username already exists"}, 400
    if User.query.filter_by(email=email).first():
        return {"error": "Email already exists"}, 400
    
    new_user = User(username=username, email=email)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()
    return {"message": "User created successfully"}, 201

def login_user(username, password):
    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return {"error": "Invalid credentials"}, 401
    
    access_token = create_access_token(identity=str(user.id))  
    return {"access_token": access_token}, 200

@jwt_required()
def get_current_user():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    return {"username": user.username, "email": user.email}, 200