from flask import Blueprint, request, jsonify, g
from app.orders.services import OrderService
from app.core.permissions import require_tenant

orders_bp = Blueprint('orders', __name__, url_prefix='/api/v1/orders')


@orders_bp.route('', methods=['GET'])
@require_tenant(min_role='STAFF')
def list_orders():
    """
    List Orders
    ---
    tags:
      - Orders
    security:
      - Bearer: []
    parameters:
      - name: X-Business-ID
        in: header
        type: string
        required: true
      - name: status
        in: query
        type: string
      - name: payment_status
        in: query
        type: string
      - name: customer_id
        in: query
        type: string
      - name: channel
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
        description: List of orders with pagination total
    """
    status = request.args.get('status')
    payment_status = request.args.get('payment_status')
    customer_id = request.args.get('customer_id')
    channel = request.args.get('channel')
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))

    orders, total = OrderService.list_orders(
        business_id=g.business_id,
        status=status,
        payment_status=payment_status,
        customer_id=customer_id,
        channel=channel,
        limit=limit,
        offset=offset
    )
    return jsonify(
        orders=[o.to_dict() for o in orders],
        total=total,
        limit=limit,
        offset=offset
    ), 200


@orders_bp.route('', methods=['POST'])
@require_tenant(min_role='STAFF')
def create_order():
    """
    Create Order
    ---
    tags:
      - Orders
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
            - customer_id
            - items
          properties:
            customer_id:
              type: string
            items:
              type: array
              items:
                type: object
                required:
                  - product_id
                  - quantity
                properties:
                  product_id:
                    type: string
                  quantity:
                    type: integer
                  unit_price:
                    type: number
            delivery_fee:
              type: number
              default: 0.0
            channel:
              type: string
              enum: [WHATSAPP, MANUAL, WEB]
              default: MANUAL
            currency:
              type: string
            delivery_address:
              type: string
            delivery_notes:
              type: string
            notes:
              type: string
    responses:
      201:
        description: Order created and stock reserved
    """
    data = request.get_json() or {}
    order = OrderService.create_order(
        business_id=g.business_id,
        customer_id=data.get('customer_id'),
        items=data.get('items'),
        delivery_fee=data.get('delivery_fee', 0.0),
        channel=data.get('channel', 'MANUAL'),
        currency=data.get('currency'),
        delivery_address=data.get('delivery_address'),
        delivery_notes=data.get('delivery_notes'),
        notes=data.get('notes')
    )
    return jsonify(order=order.to_dict()), 201


@orders_bp.route('/<order_id>', methods=['GET'])
@require_tenant(min_role='STAFF')
def get_order(order_id):
    """
    Get Order Details
    ---
    tags:
      - Orders
    security:
      - Bearer: []
    parameters:
      - name: X-Business-ID
        in: header
        type: string
        required: true
      - name: order_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Order details
    """
    order = OrderService.get_order(g.business_id, order_id)
    return jsonify(order=order.to_dict()), 200


@orders_bp.route('/<order_id>/status', methods=['PATCH'])
@require_tenant(min_role='STAFF')
def update_status(order_id):
    """
    Update Order Lifecycle Status
    ---
    tags:
      - Orders
    security:
      - Bearer: []
    parameters:
      - name: X-Business-ID
        in: header
        type: string
        required: true
      - name: order_id
        in: path
        type: string
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - status
          properties:
            status:
              type: string
              enum: [PENDING, CONFIRMED, PROCESSING, SHIPPED, DELIVERED, CANCELLED]
    responses:
      200:
        description: Order status updated
      400:
        description: Status parameter missing
    """
    data = request.get_json() or {}
    new_status = data.get('status')
    if not new_status:
        return jsonify(error="status is required"), 400

    order = OrderService.update_order_status(g.business_id, order_id, new_status)
    return jsonify(order=order.to_dict()), 200


@orders_bp.route('/<order_id>/cancel', methods=['POST'])
@require_tenant(min_role='MANAGER')
def cancel_order(order_id):
    """
    Cancel Order & Restock Inventory
    ---
    tags:
      - Orders
    security:
      - Bearer: []
    parameters:
      - name: X-Business-ID
        in: header
        type: string
        required: true
      - name: order_id
        in: path
        type: string
        required: true
      - in: body
        name: body
        schema:
          type: object
          properties:
            reason:
              type: string
    responses:
      200:
        description: Order cancelled and stock restored
    """
    data = request.get_json() or {}
    reason = data.get('reason')
    order = OrderService.cancel_order(g.business_id, order_id, reason=reason)
    return jsonify(order=order.to_dict(), message="Order cancelled and inventory restored"), 200
