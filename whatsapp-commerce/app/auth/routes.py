from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import (create_access_token, jwt_required,
                                get_jwt_identity)
from app.auth.services import AuthService

auth_bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    email = data.get('email'); password = data.get('password')
    if not email or not password:
        return jsonify(error="email and password required"), 400
    try:
        user = AuthService.register(email, password,
                                    data.get('full_name'), data.get('phone'))
    except ValueError as e:
        return jsonify(error=str(e)), 409
    token = create_access_token(identity=user.id)
    return jsonify(user=user.to_dict(), access_token=token), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    user = AuthService.authenticate(data.get('email'), data.get('password'))
    if not user:
        return jsonify(error="Invalid credentials"), 401
    token = create_access_token(identity=user.id)
    return jsonify(user=user.to_dict(), access_token=token)


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    user = AuthService.get_user(get_jwt_identity())
    return jsonify(user=user.to_dict())