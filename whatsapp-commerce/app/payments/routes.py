from flask import Blueprint, request, jsonify, g
from app.payments.services import PaymentService
from app.core.permissions import require_tenant

payments_bp = Blueprint('payments', __name__, url_prefix='/api/v1/payments')


@payments_bp.route('', methods=['GET'])
@require_tenant(min_role='STAFF')
def list_payments():
    """
    List Payments
    ---
    tags:
      - Payments
    security:
      - Bearer: []
    parameters:
      - name: X-Business-ID
        in: header
        type: string
        required: true
      - name: order_id
        in: query
        type: string
      - name: status
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
        description: List of payment transactions
    """
    order_id = request.args.get('order_id')
    status = request.args.get('status')
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))

    payments, total = PaymentService.list_payments(
        business_id=g.business_id,
        order_id=order_id,
        status=status,
        limit=limit,
        offset=offset
    )
    return jsonify(
        payments=[p.to_dict() for p in payments],
        total=total,
        limit=limit,
        offset=offset
    ), 200


@payments_bp.route('/record', methods=['POST'])
@require_tenant(min_role='STAFF')
def record_payment():
    """
    Record Payment Transaction
    ---
    tags:
      - Payments
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
            - order_id
            - amount
            - reference
          properties:
            order_id:
              type: string
            amount:
              type: number
            reference:
              type: string
            provider:
              type: string
              default: MANUAL
            payment_method:
              type: string
              default: CASH
            status:
              type: string
              default: SUCCESS
            details:
              type: object
    responses:
      201:
        description: Payment recorded and order payment status updated
      400:
        description: Missing required fields
    """
    data = request.get_json() or {}
    order_id = data.get('order_id')
    amount = data.get('amount')
    reference = data.get('reference')
    if not order_id or amount is None or not reference:
        return jsonify(error="order_id, amount, and reference are required"), 400

    payment = PaymentService.record_payment(
        business_id=g.business_id,
        order_id=order_id,
        amount=amount,
        reference=reference,
        provider=data.get('provider', 'MANUAL'),
        payment_method=data.get('payment_method', 'CASH'),
        status=data.get('status', 'SUCCESS'),
        payment_channel_details=data.get('details')
    )
    return jsonify(payment=payment.to_dict()), 201


@payments_bp.route('/<payment_id>', methods=['GET'])
@require_tenant(min_role='STAFF')
def get_payment(payment_id):
    """
    Get Payment Transaction Details
    ---
    tags:
      - Payments
    security:
      - Bearer: []
    parameters:
      - name: X-Business-ID
        in: header
        type: string
        required: true
      - name: payment_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Payment details
    """
    payment = PaymentService.get_payment(g.business_id, payment_id)
    return jsonify(payment=payment.to_dict()), 200


@payments_bp.route('/config', methods=['GET'])
@require_tenant(min_role='ADMIN')
def get_payment_config():
    """
    Get Business Payment Provider Configuration
    ---
    tags:
      - Payments
    security:
      - Bearer: []
    parameters:
      - name: X-Business-ID
        in: header
        type: string
        required: true
    responses:
      200:
        description: Payment config details
    """
    config = PaymentService.get_payment_config(g.business_id)
    return jsonify(config=config.to_dict() if config else None), 200


@payments_bp.route('/config', methods=['POST'])
@require_tenant(min_role='ADMIN')
def set_payment_config():
    """
    Configure Payment Gateway Settings (Paystack / PayPal)
    ---
    tags:
      - Payments
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
          properties:
            provider:
              type: string
              default: PAYSTACK
            public_key:
              type: string
            secret_key:
              type: string
            subaccount_code:
              type: string
            paypal_email:
              type: string
            paypal_client_id:
              type: string
            paypal_client_secret:
              type: string
            paypal_mode:
              type: string
              default: sandbox
            is_active:
              type: boolean
              default: true
    responses:
      200:
        description: Payment settings updated
    """
    data = request.get_json() or {}
    config = PaymentService.set_payment_config(
        business_id=g.business_id,
        provider=data.get('provider', 'PAYSTACK'),
        public_key=data.get('public_key'),
        secret_key=data.get('secret_key'),
        subaccount_code=data.get('subaccount_code'),
        paypal_email=data.get('paypal_email'),
        paypal_client_id=data.get('paypal_client_id'),
        paypal_client_secret=data.get('paypal_client_secret'),
        paypal_mode=data.get('paypal_mode', 'sandbox'),
        is_active=data.get('is_active', True)
    )
    return jsonify(config=config.to_dict()), 200
