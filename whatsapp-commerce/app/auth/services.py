from app.extensions import db
from app.auth.models import User
from werkzeug.security import generate_password_hash, check_password_hash
from app.core.exceptions import ConflictError


class AuthService:

    @staticmethod
    def register(email, password, full_name=None, phone=None):
        if User.query.filter_by(email=email).first():
            raise ConflictError("Email already registered")
        user = User(
            email=email,
            password_hash=generate_password_hash(password),
            full_name=full_name,
            phone=phone
        )
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def authenticate(email, password):
        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password_hash, password):
            return None
        return user

    @staticmethod
    def get_user(user_id):
        return db.session.get(User, user_id)