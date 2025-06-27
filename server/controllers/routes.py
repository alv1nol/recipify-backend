import os
from flask import request, jsonify, send_from_directory
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from datetime import datetime

from server.models import db, User, Recipe, Comment, Like
from server.auth import register_user, login_user, get_current_user

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_routes(app):
    # Upload Setup
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)


    # Upload
    @app.route('/api/upload', methods=['POST'])
    @jwt_required()
    def upload_image():
        if 'image' not in request.files:
            print("[UPLOAD] Missing 'image' field")
            return jsonify({'error': 'No image field in request'}), 400

        file = request.files['image']
        print("[UPLOAD] Got file:", file.filename)

        if not file or file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if allowed_file(file.filename):
            filename = secure_filename(file.filename)
            print("[UPLOAD] File allowed, saving as:", filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            return jsonify({'url': f'/uploads/{filename}'}), 200

        print("[UPLOAD] Disallowed file type:", file.filename)
        return jsonify({'error': 'Invalid file type. Allowed: png, jpg, jpeg, gif'}), 422

    # Recipes
    @app.route('/api/recipes', methods=['GET', 'POST'])
    @jwt_required()
    def recipes():
        if request.method == 'GET':
            recipes = Recipe.query.all()
            return jsonify([{
                'id': r.id,
                'title': r.title,
                'image_url': r.image_url,
                'user_id': r.user_id
            } for r in recipes]), 200

        elif request.method == 'POST':
            data = request.get_json()
            new_recipe = Recipe(
                title=data['title'],
                ingredients=data['ingredients'],
                instructions=data['instructions'],
                image_url=data.get('image_url', ''),
                user_id=get_jwt_identity()
            )
            db.session.add(new_recipe)
            db.session.commit()
            return jsonify({"message": "Recipe created"}), 201

    @app.route('/api/recipes/<int:recipe_id>', methods=['GET', 'PUT', 'DELETE'])
    @jwt_required()
    def recipe_detail(recipe_id):
        recipe = Recipe.query.get_or_404(recipe_id)

        if request.method == 'GET':
            return jsonify({
                'id': recipe.id,
                'title': recipe.title,
                'ingredients': recipe.ingredients,
                'instructions': recipe.instructions,
                'image_url': recipe.image_url,
                'user_id': recipe.user_id,
                'comments': [{
                    'id': c.id,
                    'text': c.text,
                    'user_id': c.user_id
                } for c in recipe.comments]
            }), 200

        elif request.method == 'PUT':
            if recipe.user_id != get_jwt_identity():
                return jsonify({"message": "Unauthorized"}), 403
            data = request.get_json()
            recipe.title = data.get('title', recipe.title)
            recipe.ingredients = data.get('ingredients', recipe.ingredients)
            recipe.instructions = data.get('instructions', recipe.instructions)
            recipe.image_url = data.get('image_url', recipe.image_url)
            db.session.commit()
            return jsonify({"message": "Recipe updated"}), 200

        elif request.method == 'DELETE':
            if recipe.user_id != get_jwt_identity():
                return jsonify({"message": "Unauthorized"}), 403
            db.session.delete(recipe)
            db.session.commit()
            return jsonify({"message": "Recipe deleted"}), 200

    # Comments
    @app.route('/api/comments/<int:recipe_id>', methods=['POST'])
    @jwt_required()
    def add_comment(recipe_id):
        data = request.get_json()
        new_comment = Comment(
            text=data['text'],
            user_id=get_jwt_identity(),
            recipe_id=recipe_id
        )
        db.session.add(new_comment)
        db.session.commit()
        return jsonify({"message": "Comment added"}), 201

    @app.route('/api/comments/<int:comment_id>', methods=['DELETE'])
    @jwt_required()
    def delete_comment(comment_id):
        comment = Comment.query.get_or_404(comment_id)
        if comment.user_id != get_jwt_identity():
            return jsonify({"message": "Unauthorized"}), 403
        db.session.delete(comment)
        db.session.commit()
        return jsonify({"message": "Comment deleted"}), 200

    # Likes
    @app.route('/api/likes/<int:recipe_id>', methods=['POST'])
    @jwt_required()
    def like_recipe(recipe_id):
        user_id = get_jwt_identity()
        existing = Like.query.filter_by(user_id=user_id, recipe_id=recipe_id).first()
        if existing:
            return jsonify({'message': 'Already liked'}), 400

        new_like = Like(user_id=user_id, recipe_id=recipe_id, created_at=datetime.utcnow())
        db.session.add(new_like)
        db.session.commit()
        return jsonify({'message': 'Recipe liked!'}), 201

    @app.route('/api/likes/<int:recipe_id>', methods=['DELETE'])
    @jwt_required()
    def unlike_recipe(recipe_id):
        user_id = get_jwt_identity()
        like = Like.query.filter_by(user_id=user_id, recipe_id=recipe_id).first()
        if not like:
            return jsonify({'message': 'Like not found'}), 404

        db.session.delete(like)
        db.session.commit()
        return jsonify({'message': 'Like removed'}), 200

    @app.route('/api/likes', methods=['GET'])
    @jwt_required()
    def get_likes():
        user_id = get_jwt_identity()
        likes = Like.query.filter_by(user_id=user_id).all()
        return jsonify([{
            'id': like.id,
            'recipe_id': like.recipe_id,
            'timestamp': like.created_at.strftime('%Y-%m-%d %H:%M:%S')
        } for like in likes]), 200

    # Users
    @app.route('/api/users', methods=['GET'])
    @jwt_required()
    def get_users():
        users = User.query.all()
        return jsonify([{
            'id': u.id,
            'username': u.username,
            'email': u.email
        } for u in users]), 200

    @app.route('/api/users/<int:user_id>', methods=['GET', 'PUT', 'DELETE'])
    @jwt_required()
    def user_detail(user_id):
        current_user_id = get_jwt_identity()
        user = User.query.get_or_404(user_id)

        if request.method == 'GET':
            return jsonify({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'recipes': [{
                    'id': r.id,
                    'title': r.title
                } for r in user.recipes]
            }), 200

        elif request.method == 'PUT':
            if current_user_id != user_id:
                return jsonify({"message": "Unauthorized"}), 403
            data = request.get_json()
            user.username = data.get('username', user.username)
            user.email = data.get('email', user.email)
            if 'password' in data:
                user.set_password(data['password'])
            db.session.commit()
            return jsonify({"message": "User updated"}), 200

        elif request.method == 'DELETE':
            if current_user_id != user_id:
                return jsonify({"message": "Unauthorized"}), 403
            db.session.delete(user)
            db.session.commit()
            return jsonify({"message": "User deleted"}), 200
        
    # Auth #
    @app.route('/api/register', methods=['POST'])
    def register():
        data = request.get_json() or {}

        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        if not username or not email or not password:
            return jsonify({'message': 'Username, email, and password are required'}), 400

        return register_user(username, email, password)
    
    # LOGIN #
    @app.route('/api/login', methods=['POST'])
    def login():
        data = request.get_json() or {}

        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({'message': 'Username and password are required'}), 400

        return login_user(username, password)
    
  
    
