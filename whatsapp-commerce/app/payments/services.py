from datetime import datetime, timezone
from decimal import Decimal
from app.extensions import db
from app.payments.models import Payment, BusinessPaymentConfig
from app.orders.models import Order
from app.core.exceptions import ResourceNotFoundError, ValidationError, ConflictError


class PaymentService:

    @staticmethod
    def set_payment_config(business_id, provider='PAYSTACK', public_key=None,
                           secret_key=None, subaccount_code=None,
                           paypal_email=None, paypal_client_id=None,
                           paypal_client_secret=None, paypal_mode='sandbox',
                           is_active=True):
        config = BusinessPaymentConfig.query.filter_by(business_id=business_id).first()
        if not config:
            config = BusinessPaymentConfig(
                business_id=business_id,
                provider=provider,
                public_key=public_key,
                secret_key_encrypted=secret_key,
                subaccount_code=subaccount_code,
                paypal_email=paypal_email,
                paypal_client_id=paypal_client_id,
                paypal_client_secret_encrypted=paypal_client_secret,
                paypal_mode=paypal_mode,
                is_active=is_active
            )
            db.session.add(config)
        else:
            config.provider = provider
            if public_key is not None:
                config.public_key = public_key
            if secret_key is not None:
                config.secret_key_encrypted = secret_key
            if subaccount_code is not None:
                config.subaccount_code = subaccount_code
            if paypal_email is not None:
                config.paypal_email = paypal_email
            if paypal_client_id is not None:
                config.paypal_client_id = paypal_client_id
            if paypal_client_secret is not None:
                config.paypal_client_secret_encrypted = paypal_client_secret
            if paypal_mode is not None:
                config.paypal_mode = paypal_mode
            config.is_active = is_active

        db.session.commit()
        return config

    @staticmethod
    def get_payment_config(business_id):
        return BusinessPaymentConfig.query.filter_by(business_id=business_id).first()

    @staticmethod
    def record_payment(business_id, order_id, amount, reference,
                       provider='MANUAL', payment_method='CASH',
                       status='SUCCESS', payment_channel_details=None):
        order = Order.query.filter_by(id=order_id, business_id=business_id).first()
        if not order:
            raise ResourceNotFoundError(f"Order {order_id} not found in this business")

        existing = Payment.query.filter_by(business_id=business_id, reference=reference).first()
        if existing:
            raise ConflictError(f"Payment reference '{reference}' already exists for this business")

        amount_dec = Decimal(str(amount))
        paid_at = datetime.now(timezone.utc) if status == 'SUCCESS' else None

        payment = Payment(
            business_id=business_id,
            order_id=order_id,
            provider=provider,
            reference=reference,
            amount=amount_dec,
            currency=order.currency,
            status=status,
            payment_method=payment_method,
            payment_channel_details=payment_channel_details,
            paid_at=paid_at
        )
        db.session.add(payment)

        if status == 'SUCCESS':
            order.payment_status = 'PAID'
            if order.status == 'PENDING':
                order.status = 'CONFIRMED'

        db.session.commit()
        return payment

    @staticmethod
    def get_payment(business_id, payment_id):
        payment = Payment.query.filter_by(id=payment_id, business_id=business_id).first()
        if not payment:
            raise ResourceNotFoundError(f"Payment {payment_id} not found in this business")
        return payment

    @staticmethod
    def list_payments(business_id, order_id=None, status=None, limit=50, offset=0):
        query = Payment.query.filter_by(business_id=business_id)
        if order_id:
            query = query.filter_by(order_id=order_id)
        if status:
            query = query.filter_by(status=status)

        total = query.count()
        payments = query.order_by(Payment.created_at.desc()).offset(offset).limit(limit).all()
        return payments, total

    @staticmethod
    def settle_payment_by_reference(business_id, reference, channel_details=None):
        payment = Payment.query.filter_by(business_id=business_id, reference=reference).first()
        if not payment:
            raise ResourceNotFoundError(f"Payment with reference {reference} not found")

        payment.status = 'SUCCESS'
        payment.paid_at = datetime.now(timezone.utc)
        if channel_details:
            payment.payment_channel_details = channel_details

        order = payment.order
        if order:
            order.payment_status = 'PAID'
            if order.status == 'PENDING':
                order.status = 'CONFIRMED'

        db.session.commit()
        return payment
