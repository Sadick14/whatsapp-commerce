from app.extensions import db
from app.customers.models import Customer
from app.core.exceptions import ResourceNotFoundError, ValidationError


def normalize_phone(phone):
    if not phone:
        return ""
    # strip non-numeric except leading +
    cleaned = phone.strip()
    if cleaned.startswith('+'):
        return '+' + ''.join(c for c in cleaned[1:] if c.isdigit())
    return ''.join(c for c in cleaned if c.isdigit())


class CustomerService:

    @staticmethod
    def get_or_create_by_phone(business_id, phone, name=None, default_delivery_address=None):
        clean_phone = normalize_phone(phone)
        if not clean_phone:
            raise ValidationError("Valid phone number required")

        customer = Customer.query.filter_by(business_id=business_id, phone=clean_phone).first()
        if not customer:
            customer = Customer(
                business_id=business_id,
                phone=clean_phone,
                name=name,
                default_delivery_address=default_delivery_address
            )
            db.session.add(customer)
            db.session.commit()
        else:
            updated = False
            if name and not customer.name:
                customer.name = name
                updated = True
            if default_delivery_address and not customer.default_delivery_address:
                customer.default_delivery_address = default_delivery_address
                updated = True
            if updated:
                db.session.commit()

        return customer

    @staticmethod
    def get_customer(business_id, customer_id):
        customer = Customer.query.filter_by(id=customer_id, business_id=business_id).first()
        if not customer:
            raise ResourceNotFoundError(f"Customer {customer_id} not found in this business")
        return customer

    @staticmethod
    def list_customers(business_id, search=None, limit=50, offset=0):
        query = Customer.query.filter_by(business_id=business_id)
        if search:
            query = query.filter(
                (Customer.phone.ilike(f"%{search}%")) |
                (Customer.name.ilike(f"%{search}%"))
            )
        total = query.count()
        customers = query.order_by(Customer.created_at.desc()).offset(offset).limit(limit).all()
        return customers, total

    @staticmethod
    def update_customer(business_id, customer_id, **kwargs):
        customer = CustomerService.get_customer(business_id, customer_id)
        allowed = {'name', 'default_delivery_address'}
        for k, v in kwargs.items():
            if k in allowed and v is not None:
                setattr(customer, k, v)
        db.session.commit()
        return customer

    @staticmethod
    def record_order_stats(business_id, customer_id, order_total):
        customer = CustomerService.get_customer(business_id, customer_id)
        customer.total_orders += 1
        customer.total_spent = (customer.total_spent or 0) + order_total
        db.session.commit()
        return customer
