from functools import wraps
from flask import request, jsonify, g
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from app.auth.models import BusinessMember
from app.core.exceptions import PermissionDeniedError, TenantViolationError, ValidationError

ROLE_HIERARCHY = {
    'OWNER': 4,
    'ADMIN': 3,
    'MANAGER': 2,
    'STAFF': 1
}


def require_tenant(min_role='STAFF'):
    """
    Ensures valid JWT, extracts business_id from header (X-Business-ID) or route/query,
    verifies user belongs to the business with sufficient role, and injects context:
    g.user_id, g.business_id, g.member_role, g.business.
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            verify_jwt_in_request()
            user_id = get_jwt_identity()

            business_id = (
                kwargs.get('business_id') or
                request.headers.get('X-Business-ID') or
                request.args.get('business_id')
            )

            if not business_id:
                raise ValidationError("X-Business-ID header or business_id parameter required")

            membership = BusinessMember.query.filter_by(
                business_id=business_id,
                user_id=user_id
            ).first()

            if not membership:
                raise TenantViolationError("Access denied to this business workspace")

            user_role_level = ROLE_HIERARCHY.get(membership.role, 0)
            required_role_level = ROLE_HIERARCHY.get(min_role, 0)

            if user_role_level < required_role_level:
                raise PermissionDeniedError(
                    f"Insufficient permissions. Required: {min_role}, current: {membership.role}"
                )

            g.user_id = user_id
            g.business_id = business_id
            g.member_role = membership.role
            g.business = membership.business

            return f(*args, **kwargs)
        return decorated
    return decorator


def has_role_or_higher(current_role, required_role):
    return ROLE_HIERARCHY.get(current_role, 0) >= ROLE_HIERARCHY.get(required_role, 0)
