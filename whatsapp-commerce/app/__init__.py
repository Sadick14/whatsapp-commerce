import os
from flask import Flask, jsonify
from sqlalchemy import event
from sqlalchemy.engine import Engine
from app.extensions import db, migrate, jwt, swagger
from app.config import config
from app.core.exceptions import AppError
import app.models  # noqa: F401


@event.listens_for(Engine, "connect")
def set_sqlite_pragmas(dbapi_connection, connection_record):
    if dbapi_connection.__class__.__module__.startswith("sqlite3"):
        cur = dbapi_connection.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.execute("PRAGMA journal_mode=WAL")
        cur.execute("PRAGMA synchronous=NORMAL")
        cur.execute("PRAGMA busy_timeout=5000")
        cur.close()


swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec',
            "route": '/api/docs.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/api/docs"
}

swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "WhatsApp Commerce API",
        "description": "API documentation for Multi-Tenant WhatsApp E-Commerce Platform",
        "version": "1.0.0"
    },
    "basePath": "/",
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "JWT Authorization header using the Bearer scheme. Example: \"Authorization: Bearer {token}\""
        }
    },
    "security": [
        {
            "Bearer": []
        }
    ]
}


def create_app(config_name='default'):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config[config_name])
    
    os.makedirs(app.instance_path, exist_ok=True)

    app.config['SWAGGER'] = swagger_config
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    swagger.template = swagger_template
    swagger.init_app(app)

    register_blueprints(app)
    register_error_handlers(app)

    from app.cli import register_cli
    register_cli(app)

    return app


def register_blueprints(app):
    from app.auth.routes import auth_bp
    from app.businesses.routes import businesses_bp
    from app.products.routes import products_bp
    from app.customers.routes import customers_bp
    from app.orders.routes import orders_bp
    from app.payments.routes import payments_bp
    from app.whatsapp.routes import whatsapp_bp
    from app.webhooks.whatsapp import whatsapp_webhook_bp
    from app.webhooks.payments import payments_webhook_bp

    for bp in (auth_bp, businesses_bp, products_bp, customers_bp,
               orders_bp, payments_bp, whatsapp_bp,
               whatsapp_webhook_bp, payments_webhook_bp):
        app.register_blueprint(bp)


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(e):
        return jsonify(e.to_dict()), e.status_code

    @app.errorhandler(404)
    def not_found(e):
        return jsonify(error=getattr(e, 'description', "Not found")), 404

    @app.errorhandler(403)
    def forbidden(e):
        return jsonify(error=getattr(e, 'description', "Forbidden")), 403

    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify(error=getattr(e, 'description', "Unauthorized")), 401

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify(error=getattr(e, 'description', "Bad request")), 400

    @app.errorhandler(409)
    def conflict(e):
        return jsonify(error=getattr(e, 'description', "Conflict")), 409