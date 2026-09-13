from app.extensions import db
from app.core.base_model import gen_uuid, TimestampMixin

class Business(db.Model, TimestampMixin):
    __tablename__ = 'businesses'

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    name = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), unique=True, nullable=False, index=True)
    owner_id = db.Column(
        db.String(36),
        db.ForeignKey('users.id', ondelete='RESTRICT'),
        nullable=False
    )
    currency = db.Column(db.String(3), default='GHS', nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(255))
    address = db.Column(db.Text)
    logo_url = db.Column(db.Text)
    status = db.Column(db.String(20), default='ACTIVE', nullable=False)
    plan = db.Column(db.String(20), default='FREE', nullable=False)

    members = db.relationship(
        'BusinessMember',
        back_populates='business',
        cascade='all, delete-orphan'
    )
    whatsapp_account = db.relationship(
        'BusinessWhatsAppAccount',
        back_populates='business',
        uselist=False,
        cascade='all, delete-orphan'
    )
    payment_config = db.relationship(
        'BusinessPaymentConfig',
        back_populates='business',
        uselist=False,
        cascade='all, delete-orphan'
    )

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'owner_id': self.owner_id,
            'currency': self.currency,
            'phone': self.phone,
            'email': self.email,
            'address': self.address,
            'logo_url': self.logo_url,
            'status': self.status,
            'plan': self.plan,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }