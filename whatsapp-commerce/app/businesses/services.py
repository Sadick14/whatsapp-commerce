import re
from app.extensions import db
from app.businesses.models import Business
from app.auth.models import BusinessMember, User
from app.core.exceptions import ResourceNotFoundError, ConflictError, ValidationError


def slugify(text):
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    return re.sub(r'[-\s]+', '-', text)


class BusinessService:

    @staticmethod
    def create_business(owner_id, name, slug=None, currency='GHS', phone=None,
                        email=None, address=None, logo_url=None):
        if not name:
            raise ValidationError("Business name is required")

        base_slug = slugify(slug or name)
        candidate_slug = base_slug
        count = 1
        while Business.query.filter_by(slug=candidate_slug).first():
            candidate_slug = f"{base_slug}-{count}"
            count += 1

        business = Business(
            name=name,
            slug=candidate_slug,
            owner_id=owner_id,
            currency=currency,
            phone=phone,
            email=email,
            address=address,
            logo_url=logo_url,
            status='ACTIVE',
            plan='FREE'
        )
        db.session.add(business)
        db.session.flush()

        member = BusinessMember(
            business_id=business.id,
            user_id=owner_id,
            role='OWNER'
        )
        db.session.add(member)
        db.session.commit()
        return business

    @staticmethod
    def list_user_businesses(user_id):
        memberships = BusinessMember.query.filter_by(user_id=user_id).all()
        result = []
        for m in memberships:
            biz_dict = m.business.to_dict()
            biz_dict['my_role'] = m.role
            result.append(biz_dict)
        return result

    @staticmethod
    def get_business(business_id):
        biz = db.session.get(Business, business_id)
        if not biz:
            raise ResourceNotFoundError(f"Business {business_id} not found")
        return biz

    @staticmethod
    def update_business(business_id, **kwargs):
        biz = BusinessService.get_business(business_id)
        allowed_fields = {'name', 'currency', 'phone', 'email', 'address', 'logo_url', 'status', 'plan'}
        for field, value in kwargs.items():
            if field in allowed_fields and value is not None:
                setattr(biz, field, value)
        db.session.commit()
        return biz

    @staticmethod
    def list_members(business_id):
        return BusinessMember.query.filter_by(business_id=business_id).all()

    @staticmethod
    def add_member(business_id, user_email, role='STAFF', invited_by=None):
        if role not in ('OWNER', 'ADMIN', 'MANAGER', 'STAFF'):
            raise ValidationError(f"Invalid role: {role}")

        user = User.query.filter_by(email=user_email).first()
        if not user:
            raise ResourceNotFoundError(f"User with email {user_email} not found")

        existing = BusinessMember.query.filter_by(business_id=business_id, user_id=user.id).first()
        if existing:
            raise ConflictError(f"User is already a member of this business with role {existing.role}")

        member = BusinessMember(
            business_id=business_id,
            user_id=user.id,
            role=role,
            invited_by=invited_by
        )
        db.session.add(member)
        db.session.commit()
        return member

    @staticmethod
    def remove_member(business_id, user_id):
        member = BusinessMember.query.filter_by(business_id=business_id, user_id=user_id).first()
        if not member:
            raise ResourceNotFoundError("Member not found in this business")
        if member.role == 'OWNER':
            raise ValidationError("Cannot remove the business OWNER")

        db.session.delete(member)
        db.session.commit()
        return True
