from app.extensions import db
from app.core.base_model import gen_uuid, TimestampMixin

class User(db.Model, TimestampMixin):
    __tablename__ = 'users'

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(255))
    phone = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    memberships = db.relationship('BusinessMember', back_populates='user',
                                  foreign_keys='BusinessMember.user_id',
                                  cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'full_name': self.full_name,
            'phone': self.phone,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class BusinessMember(db.Model):
    __tablename__ = 'business_members'

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    business_id = db.Column(db.String(36),
        db.ForeignKey('businesses.id', ondelete='CASCADE'),
        nullable=False, index=True)
    user_id = db.Column(db.String(36),
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False, index=True)
    role = db.Column(db.String(20), nullable=False, default='STAFF')
    invited_by = db.Column(db.String(36), db.ForeignKey('users.id'))
    joined_at = db.Column(db.DateTime, default=db.func.now())

    user = db.relationship('User', back_populates='memberships', foreign_keys=[user_id])
    business = db.relationship('Business', back_populates='members')

    __table_args__ = (
        db.UniqueConstraint('business_id', 'user_id', name='uq_member'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'business_id': self.business_id,
            'user_id': self.user_id,
            'role': self.role,
            'user': self.user.to_dict() if self.user else None,
            'joined_at': self.joined_at.isoformat() if self.joined_at else None
        }