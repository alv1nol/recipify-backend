import os
from flask import request, jsonify, send_from_directory
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from server.models import db, User, Recipe, Comment
from server.auth import register_user, login_user, get_current_user

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_routes(app):
    # UPLOAD SETUP
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    # AUTH 
    @app.route('/api/register', methods=['POST'])
    def register():
        data = request.get_json()
        return register_user(data['username'], data['email'], data['password'])

    @app.route('/api/login', methods=['POST'])
    def login():
        data = request.get_json()
        return login_user(data['username'], data['password'])

    @app.route('/api/profile', methods=['GET'])
    @jwt_required()
    def profile():
        return get_current_user()

    # UPLOAD 
@app.route('/api/upload', methods=['POST'])
@jwt_required()
def upload_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image part'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        image_url = f"/uploads/{filename}"
        return jsonify({'url': image_url}), 200

    return jsonify({'error': 'Invalid file type'}), 400

    @app.route('/uploads/<filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    # RECIPES
    @app.route('/api/recipes', methods=['GET', 'POST'])
    @jwt_required()
    def recipes():
        if request.method == 'GET':
            recipes = Recipe.query.all()
            return jsonify([{
                'id': r.id,
                'title': r.title,
                'image_url': r.image_url
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

    #  RECIPE DETAIL 
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

    # COMMENTS 
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

    #  USERS 
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
