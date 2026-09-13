import uuid
from datetime import datetime, timezone
from app.extensions import db


def gen_uuid():
    return str(uuid.uuid4())


def utc_now():
    return datetime.now(timezone.utc)


class TimestampMixin:
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now, nullable=False)


class TenantMixin:
    business_id = db.Column(
        db.String(36),
        db.ForeignKey('businesses.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    @classmethod
    def for_business(cls, business_id):
        return cls.query.filter_by(business_id=business_id)