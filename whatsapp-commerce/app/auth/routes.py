from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import (create_access_token, jwt_required,
                                get_jwt_identity)
from app.auth.services import AuthService

auth_bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    User Registration
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - email
            - password
          properties:
            email:
              type: string
              example: user@example.com
            password:
              type: string
              example: secret123
            full_name:
              type: string
              example: Jane Doe
            phone:
              type: string
              example: "+233200000000"
    responses:
      201:
        description: User registered successfully
      400:
        description: Missing required fields
      409:
        description: User already exists
    """
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
    """
    User Login
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - email
            - password
          properties:
            email:
              type: string
              example: user@example.com
            password:
              type: string
              example: secret123
    responses:
      200:
        description: Authentication successful with JWT access token
      401:
        description: Invalid credentials
    """
    data = request.get_json() or {}
    user = AuthService.authenticate(data.get('email'), data.get('password'))
    if not user:
        return jsonify(error="Invalid credentials"), 401
    token = create_access_token(identity=user.id)
    return jsonify(user=user.to_dict(), access_token=token)


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    """
    Get Current User Profile
    ---
    tags:
      - Authentication
    security:
      - Bearer: []
    responses:
      200:
        description: User profile info
      401:
        description: Unauthorized
    """
    user = AuthService.get_user(get_jwt_identity())
    return jsonify(user=user.to_dict())