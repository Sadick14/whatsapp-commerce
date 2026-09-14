from flask import Blueprint, request, jsonify, g
from app.extensions import db
from app.customers.services import CustomerService
from app.core.permissions import require_tenant

customers_bp = Blueprint('customers', __name__, url_prefix='/api/v1/customers')


@customers_bp.route('', methods=['GET'])
@require_tenant(min_role='STAFF')
def list_customers():
    """
    List Customers
    ---
    tags:
      - Customers
    security:
      - Bearer: []
    parameters:
      - name: X-Business-ID
        in: header
        type: string
        required: true
      - name: search
        in: query
        type: string
      - name: limit
        in: query
        type: integer
        default: 50
      - name: offset
        in: query
        type: integer
        default: 0
    responses:
      200:
        description: List of customers
    """
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
    """
    Create or Get Customer by Phone
    ---
    tags:
      - Customers
    security:
      - Bearer: []
    parameters:
      - name: X-Business-ID
        in: header
        type: string
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - phone
          properties:
            phone:
              type: string
              example: "+233240000000"
            name:
              type: string
              example: John Doe
            default_delivery_address:
              type: string
              example: "45 Independence Ave, Accra"
    responses:
      201:
        description: Customer created or retrieved
      400:
        description: Missing phone parameter
    """
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
    """
    Get Customer Profile & Order History
    ---
    tags:
      - Customers
    security:
      - Bearer: []
    parameters:
      - name: X-Business-ID
        in: header
        type: string
        required: true
      - name: customer_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Customer profile with recent orders
    """
    customer = CustomerService.get_customer(g.business_id, customer_id)
    orders = [o.to_dict() for o in customer.orders.order_by(db.desc('created_at')).limit(10).all()] if hasattr(customer, 'orders') else []
    data = customer.to_dict()
    data['recent_orders'] = orders
    return jsonify(customer=data), 200


@customers_bp.route('/<customer_id>', methods=['PATCH'])
@require_tenant(min_role='STAFF')
def update_customer(customer_id):
    """
    Update Customer Details
    ---
    tags:
      - Customers
    security:
      - Bearer: []
    parameters:
      - name: X-Business-ID
        in: header
        type: string
        required: true
      - name: customer_id
        in: path
        type: string
        required: true
      - in: body
        name: body
        schema:
          type: object
          properties:
            name:
              type: string
            phone:
              type: string
            default_delivery_address:
              type: string
            notes:
              type: string
    responses:
      200:
        description: Customer profile updated
    """
    data = request.get_json() or {}
    customer = CustomerService.update_customer(g.business_id, customer_id, **data)
    return jsonify(customer=customer.to_dict()), 200
