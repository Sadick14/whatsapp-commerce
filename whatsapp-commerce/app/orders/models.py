from app.extensions import db
from app.core.base_model import gen_uuid, TimestampMixin, TenantMixin


class Order(db.Model, TimestampMixin, TenantMixin):
    __tablename__ = 'orders'

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    customer_id = db.Column(
        db.String(36),
        db.ForeignKey('customers.id', ondelete='RESTRICT'),
        nullable=False,
        index=True
    )
    order_number = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='PENDING', nullable=False)
    # PENDING -> CONFIRMED -> PROCESSING -> SHIPPED -> DELIVERED (or CANCELLED)
    payment_status = db.Column(db.String(20), default='UNPAID', nullable=False)
    # UNPAID -> PAID / PARTIALLY_PAID / REFUNDED
    channel = db.Column(db.String(20), default='WHATSAPP', nullable=False)
    # WHATSAPP, WEB, MANUAL, API
    currency = db.Column(db.String(3), default='GHS', nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), default=0.00, nullable=False)
    delivery_fee = db.Column(db.Numeric(10, 2), default=0.00, nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), default=0.00, nullable=False)
    delivery_address = db.Column(db.Text)
    delivery_notes = db.Column(db.Text)
    notes = db.Column(db.Text)

    customer = db.relationship('Customer', back_populates='orders')
    items = db.relationship('OrderItem', back_populates='order', cascade='all, delete-orphan')
    payments = db.relationship('Payment', back_populates='order', lazy='dynamic')

    __table_args__ = (
        db.UniqueConstraint('business_id', 'order_number', name='uq_biz_order_num'),
        db.Index('idx_orders_biz_status', 'business_id', 'status'),
        db.Index('idx_orders_biz_customer', 'business_id', 'customer_id'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'business_id': self.business_id,
            'customer_id': self.customer_id,
            'customer_name': self.customer.name if self.customer else None,
            'customer_phone': self.customer.phone if self.customer else None,
            'order_number': self.order_number,
            'status': self.status,
            'payment_status': self.payment_status,
            'channel': self.channel,
            'currency': self.currency,
            'subtotal': float(self.subtotal) if self.subtotal is not None else 0.0,
            'delivery_fee': float(self.delivery_fee) if self.delivery_fee is not None else 0.0,
            'total_amount': float(self.total_amount) if self.total_amount is not None else 0.0,
            'delivery_address': self.delivery_address,
            'delivery_notes': self.delivery_notes,
            'notes': self.notes,
            'items': [item.to_dict() for item in self.items],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    order_id = db.Column(
        db.String(36),
        db.ForeignKey('orders.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    product_id = db.Column(
        db.String(36),
        db.ForeignKey('products.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    product_name = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    total_price = db.Column(db.Numeric(10, 2), nullable=False)

    order = db.relationship('Order', back_populates='items')
    product = db.relationship('Product')

    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'product_id': self.product_id,
            'product_name': self.product_name,
            'quantity': self.quantity,
            'unit_price': float(self.unit_price) if self.unit_price is not None else 0.0,
            'total_price': float(self.total_price) if self.total_price is not None else 0.0
        }
