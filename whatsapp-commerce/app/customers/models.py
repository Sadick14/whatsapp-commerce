from app.extensions import db
from app.core.base_model import gen_uuid, TimestampMixin, TenantMixin


class Customer(db.Model, TimestampMixin, TenantMixin):
    __tablename__ = 'customers'

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    phone = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(255))
    default_delivery_address = db.Column(db.Text)
    total_orders = db.Column(db.Integer, default=0, nullable=False)
    total_spent = db.Column(db.Numeric(12, 2), default=0.00, nullable=False)

    orders = db.relationship('Order', back_populates='customer', lazy='dynamic')

    __table_args__ = (
        db.UniqueConstraint('business_id', 'phone', name='uq_biz_customer_phone'),
        db.Index('idx_customers_biz_phone', 'business_id', 'phone'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'business_id': self.business_id,
            'phone': self.phone,
            'name': self.name,
            'default_delivery_address': self.default_delivery_address,
            'total_orders': self.total_orders,
            'total_spent': float(self.total_spent) if self.total_spent is not None else 0.0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
