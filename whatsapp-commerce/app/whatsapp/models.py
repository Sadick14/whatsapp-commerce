from app.extensions import db
from app.core.base_model import gen_uuid, TimestampMixin, TenantMixin


class BusinessWhatsAppAccount(db.Model, TimestampMixin, TenantMixin):
    __tablename__ = 'business_whatsapp_accounts'

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    phone_number_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    display_phone_number = db.Column(db.String(30), nullable=False)
    waba_id = db.Column(db.String(100), nullable=False)
    access_token_encrypted = db.Column(db.Text)
    webhook_verify_token = db.Column(db.String(255))
    quality_rating = db.Column(db.String(50), default='UNKNOWN')
    status = db.Column(db.String(20), default='CONNECTED', nullable=False)  # CONNECTED, DISCONNECTED, PENDING

    business = db.relationship('Business', back_populates='whatsapp_account')

    __table_args__ = (
        db.UniqueConstraint('business_id', name='uq_biz_whatsapp_acc'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'business_id': self.business_id,
            'phone_number_id': self.phone_number_id,
            'display_phone_number': self.display_phone_number,
            'waba_id': self.waba_id,
            'quality_rating': self.quality_rating,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
