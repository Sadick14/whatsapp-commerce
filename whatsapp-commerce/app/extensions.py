from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flasgger import Swagger
from app.core.tenant import TenantQuery

db = SQLAlchemy(query_class=TenantQuery)
migrate = Migrate()
jwt = JWTManager()
swagger = Swagger()