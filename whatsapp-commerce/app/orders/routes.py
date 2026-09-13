from flask import Blueprint, request, jsonify, g
from app.orders.services import OrderService
from app.core.permissions import require_tenant

orders_bp = Blueprint('orders', __name__, url_prefix='/api/v1/orders')


@orders_bp.route('', methods=['GET'])
@require_tenant(min_role='STAFF')
def list_orders():
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
    order = OrderService.get_order(g.business_id, order_id)
    return jsonify(order=order.to_dict()), 200


@orders_bp.route('/<order_id>/status', methods=['PATCH'])
@require_tenant(min_role='STAFF')
def update_status(order_id):
    data = request.get_json() or {}
    new_status = data.get('status')
    if not new_status:
        return jsonify(error="status is required"), 400

    order = OrderService.update_order_status(g.business_id, order_id, new_status)
    return jsonify(order=order.to_dict()), 200


@orders_bp.route('/<order_id>/cancel', methods=['POST'])
@require_tenant(min_role='MANAGER')
def cancel_order(order_id):
    data = request.get_json() or {}
    reason = data.get('reason')
    order = OrderService.cancel_order(g.business_id, order_id, reason=reason)
    return jsonify(order=order.to_dict(), message="Order cancelled and inventory restored"), 200
