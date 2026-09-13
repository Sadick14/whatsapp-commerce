from flask import Blueprint, request, jsonify, g
from app.extensions import db
from app.customers.services import CustomerService
from app.core.permissions import require_tenant

customers_bp = Blueprint('customers', __name__, url_prefix='/api/v1/customers')


@customers_bp.route('', methods=['GET'])
@require_tenant(min_role='STAFF')
def list_customers():
    search = request.args.get('search')
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))

    customers, total = CustomerService.list_customers(
        business_id=g.business_id,
        search=search,
        limit=limit,
        offset=offset
    )
    return jsonify(
        customers=[c.to_dict() for c in customers],
        total=total,
        limit=limit,
        offset=offset
    ), 200


@customers_bp.route('', methods=['POST'])
@require_tenant(min_role='STAFF')
def create_customer():
    data = request.get_json() or {}
    phone = data.get('phone')
    if not phone:
        return jsonify(error="phone is required"), 400

    customer = CustomerService.get_or_create_by_phone(
        business_id=g.business_id,
        phone=phone,
        name=data.get('name'),
        default_delivery_address=data.get('default_delivery_address')
    )
    return jsonify(customer=customer.to_dict()), 201


@customers_bp.route('/<customer_id>', methods=['GET'])
@require_tenant(min_role='STAFF')
def get_customer(customer_id):
    customer = CustomerService.get_customer(g.business_id, customer_id)
    orders = [o.to_dict() for o in customer.orders.order_by(db.desc('created_at')).limit(10).all()] if hasattr(customer, 'orders') else []
    data = customer.to_dict()
    data['recent_orders'] = orders
    return jsonify(customer=data), 200


@customers_bp.route('/<customer_id>', methods=['PATCH'])
@require_tenant(min_role='STAFF')
def update_customer(customer_id):
    data = request.get_json() or {}
    customer = CustomerService.update_customer(g.business_id, customer_id, **data)
    return jsonify(customer=customer.to_dict()), 200
