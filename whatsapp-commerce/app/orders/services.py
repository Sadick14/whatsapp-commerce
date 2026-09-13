from decimal import Decimal
from datetime import datetime, timezone
from app.extensions import db
from app.orders.models import Order, OrderItem
from app.products.models import Product
from app.customers.models import Customer
from app.businesses.models import Business
from app.core.exceptions import ResourceNotFoundError, ValidationError, ConflictError


VALID_STATUS_TRANSITIONS = {
    'PENDING': {'CONFIRMED', 'CANCELLED'},
    'CONFIRMED': {'PROCESSING', 'CANCELLED'},
    'PROCESSING': {'SHIPPED', 'CANCELLED'},
    'SHIPPED': {'DELIVERED', 'CANCELLED'},
    'DELIVERED': set(),
    'CANCELLED': set()
}


class OrderService:

    @staticmethod
    def generate_order_number(business_id):
        count = Order.query.filter_by(business_id=business_id).count() + 1
        date_str = datetime.now(timezone.utc).strftime('%Y%m%d')
        return f"ORD-{date_str}-{count:04d}"

    @staticmethod
    def create_order(business_id, customer_id, items, delivery_fee=0.0,
                     channel='WHATSAPP', currency=None, delivery_address=None,
                     delivery_notes=None, notes=None):
        customer = Customer.query.filter_by(id=customer_id, business_id=business_id).first()
        if not customer:
            raise ResourceNotFoundError(f"Customer {customer_id} not found in this business")

        if not items or not isinstance(items, list):
            raise ValidationError("Order must contain at least one item")

        # Resolve currency from business if not supplied
        if not currency:
            biz = db.session.get(Business, business_id)
            currency = biz.currency if biz else 'GHS'

        subtotal = Decimal('0.00')
        order_items_to_add = []

        # Validate stock & reserve products
        for item_data in items:
            product_id = item_data.get('product_id')
            qty = item_data.get('quantity', 1)
            if qty <= 0:
                raise ValidationError("Item quantity must be greater than 0")

            product = Product.query.filter_by(id=product_id, business_id=business_id).first()
            if not product:
                raise ResourceNotFoundError(f"Product {product_id} not found in this business")

            if product.status != 'ACTIVE':
                raise ValidationError(f"Product '{product.name}' is currently not available for purchase")

            if product.stock_quantity < qty:
                raise ValidationError(
                    f"Insufficient stock for '{product.name}'. Available: {product.stock_quantity}, requested: {qty}"
                )

            # Deduct stock
            product.stock_quantity -= qty
            
            unit_price = Decimal(str(product.price))
            item_total = unit_price * qty
            subtotal += item_total

            order_item = OrderItem(
                product_id=product.id,
                product_name=product.name,
                quantity=qty,
                unit_price=unit_price,
                total_price=item_total
            )
            order_items_to_add.append(order_item)

        delivery_fee_dec = Decimal(str(delivery_fee or 0.0))
        total_amount = subtotal + delivery_fee_dec
        order_number = OrderService.generate_order_number(business_id)

        order = Order(
            business_id=business_id,
            customer_id=customer_id,
            order_number=order_number,
            status='PENDING',
            payment_status='UNPAID',
            channel=channel,
            currency=currency,
            subtotal=subtotal,
            delivery_fee=delivery_fee_dec,
            total_amount=total_amount,
            delivery_address=delivery_address or customer.default_delivery_address,
            delivery_notes=delivery_notes,
            notes=notes
        )
        db.session.add(order)
        db.session.flush()

        for item in order_items_to_add:
            item.order_id = order.id
            db.session.add(item)

        # Update customer quick stats
        customer.total_orders += 1
        customer.total_spent = (customer.total_spent or Decimal('0.00')) + total_amount

        db.session.commit()
        return order

    @staticmethod
    def get_order(business_id, order_id):
        order = Order.query.filter_by(id=order_id, business_id=business_id).first()
        if not order:
            raise ResourceNotFoundError(f"Order {order_id} not found in this business")
        return order

    @staticmethod
    def list_orders(business_id, status=None, payment_status=None, customer_id=None,
                    channel=None, limit=50, offset=0):
        query = Order.query.filter_by(business_id=business_id)

        if status:
            query = query.filter_by(status=status)
        if payment_status:
            query = query.filter_by(payment_status=payment_status)
        if customer_id:
            query = query.filter_by(customer_id=customer_id)
        if channel:
            query = query.filter_by(channel=channel)

        total = query.count()
        orders = query.order_by(Order.created_at.desc()).offset(offset).limit(limit).all()
        return orders, total

    @staticmethod
    def update_order_status(business_id, order_id, new_status):
        order = OrderService.get_order(business_id, order_id)
        new_status = new_status.upper()

        if new_status == order.status:
            return order

        valid_next = VALID_STATUS_TRANSITIONS.get(order.status, set())
        if new_status not in valid_next:
            raise ConflictError(
                f"Cannot transition order status from '{order.status}' to '{new_status}'"
            )

        if new_status == 'CANCELLED':
            return OrderService.cancel_order(business_id, order_id)

        order.status = new_status
        db.session.commit()
        return order

    @staticmethod
    def cancel_order(business_id, order_id, reason=None):
        order = OrderService.get_order(business_id, order_id)
        if order.status == 'CANCELLED':
            return order

        if order.status == 'DELIVERED':
            raise ValidationError("Cannot cancel an already delivered order")

        # Restore inventory
        for item in order.items:
            if item.product_id:
                product = Product.query.filter_by(id=item.product_id, business_id=business_id).first()
                if product:
                    product.stock_quantity += item.quantity

        order.status = 'CANCELLED'
        if reason:
            order.notes = f"{order.notes or ''}\nCancellation reason: {reason}".strip()

        # Adjust customer stats
        customer = order.customer
        if customer:
            customer.total_spent = max(Decimal('0.00'), (customer.total_spent or Decimal('0.00')) - order.total_amount)

        db.session.commit()
        return order
