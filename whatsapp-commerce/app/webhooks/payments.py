from flask import Blueprint, request, jsonify
from app.payments.services import PaymentService
from app.payments.models import Payment

payments_webhook_bp = Blueprint('payments_webhook', __name__, url_prefix='/api/v1/webhooks/payments')


@payments_webhook_bp.route('/paystack', methods=['POST'])
def paystack_webhook():
    """
    Paystack Payment Webhook Callback
    ---
    tags:
      - Webhooks
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            event:
              type: string
              example: charge.success
            data:
              type: object
              properties:
                reference:
                  type: string
    responses:
      200:
        description: Webhook processed and payment settled if matching reference found
    """
    payload = request.get_json() or {}
    event = payload.get('event')
    data = payload.get('data', {})

    if event == 'charge.success':
        reference = data.get('reference')
        # Find payment by reference
        payment = Payment.query.filter_by(reference=reference).first()
        if payment:
            PaymentService.settle_payment_by_reference(
                business_id=payment.business_id,
                reference=reference,
                channel_details=data
            )
            return jsonify(status="success", message="Payment settled"), 200

    return jsonify(status="ignored"), 200
