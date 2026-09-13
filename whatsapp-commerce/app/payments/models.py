from app.extensions import db
from app.core.base_model import gen_uuid, TimestampMixin, TenantMixin


class BusinessPaymentConfig(db.Model, TimestampMixin, TenantMixin):
    __tablename__ = 'business_payment_configs'

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    provider = db.Column(db.String(50), default='PAYSTACK', nullable=False)
    public_key = db.Column(db.String(255))
    secret_key_encrypted = db.Column(db.Text)
    subaccount_code = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    business = db.relationship('Business', back_populates='payment_config')

    __table_args__ = (
        db.UniqueConstraint('business_id', name='uq_biz_payment_config'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'business_id': self.business_id,
            'provider': self.provider,
            'public_key': self.public_key,
            'subaccount_code': self.subaccount_code,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Payment(db.Model, TimestampMixin, TenantMixin):
    __tablename__ = 'payments'

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    order_id = db.Column(
        db.String(36),
        db.ForeignKey('orders.id', ondelete='RESTRICT'),
        nullable=False,
        index=True
    )
    provider = db.Column(db.String(50), default='PAYSTACK', nullable=False)
    reference = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), default='GHS', nullable=False)
    status = db.Column(db.String(20), default='INITIALIZED', nullable=False)
    # INITIALIZED, SUCCESS, FAILED, REFUNDED
    payment_method = db.Column(db.String(50))  # MOBILE_MONEY, CARD, CASH
    payment_channel_details = db.Column(db.JSON)
    paid_at = db.Column(db.DateTime)

    order = db.relationship('Order', back_populates='payments')

    __table_args__ = (
        db.UniqueConstraint('business_id', 'reference', name='uq_biz_payment_ref'),
        db.Index('idx_payments_biz_order', 'business_id', 'order_id'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'business_id': self.business_id,
            'order_id': self.order_id,
            'provider': self.provider,
            'reference': self.reference,
            'amount': float(self.amount) if self.amount is not None else 0.0,
            'currency': self.currency,
            'status': self.status,
            'payment_method': self.payment_method,
            'payment_channel_details': self.payment_channel_details,
            'paid_at': self.paid_at.isoformat() if self.paid_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
