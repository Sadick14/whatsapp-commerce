import re
from app.extensions import db
from app.products.models import Product, ProductCategory
from app.core.exceptions import ResourceNotFoundError, ValidationError


def slugify(text):
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    return re.sub(r'[-\s]+', '-', text)


class ProductService:

    @staticmethod
    def create_category(business_id, name, slug=None):
        if not name:
            raise ValidationError("Category name is required")
        cat_slug = slugify(slug or name)
        
        existing = ProductCategory.query.filter_by(business_id=business_id, slug=cat_slug).first()
        if existing:
            return existing

        category = ProductCategory(
            business_id=business_id,
            name=name,
            slug=cat_slug
        )
        db.session.add(category)
        db.session.commit()
        return category

    @staticmethod
    def list_categories(business_id):
        return ProductCategory.query.filter_by(business_id=business_id).all()

    @staticmethod
    def create_product(business_id, name, price, category_id=None, description=None,
                       sku=None, cost_price=None, stock_quantity=0,
                       low_stock_threshold=5, image_url=None, status='ACTIVE'):
        if not name:
            raise ValidationError("Product name is required")
        if price is None or float(price) < 0:
            raise ValidationError("Product price must be a non-negative number")

        if category_id:
            cat = ProductCategory.query.filter_by(id=category_id, business_id=business_id).first()
            if not cat:
                raise ResourceNotFoundError(f"Category {category_id} not found for this business")

        product = Product(
            business_id=business_id,
            category_id=category_id,
            name=name,
            description=description,
            sku=sku,
            price=price,
            cost_price=cost_price,
            stock_quantity=stock_quantity,
            low_stock_threshold=low_stock_threshold,
            image_url=image_url,
            status=status
        )
        db.session.add(product)
        db.session.commit()
        return product

    @staticmethod
    def get_product(business_id, product_id):
        product = Product.query.filter_by(id=product_id, business_id=business_id).first()
        if not product:
            raise ResourceNotFoundError(f"Product {product_id} not found in this business")
        return product

    @staticmethod
    def list_products(business_id, category_id=None, status=None, search=None,
                      low_stock=False, limit=50, offset=0):
        query = Product.query.filter_by(business_id=business_id)

        if category_id:
            query = query.filter_by(category_id=category_id)
        if status:
            query = query.filter_by(status=status)
        if search:
            query = query.filter(
                (Product.name.ilike(f"%{search}%")) |
                (Product.sku.ilike(f"%{search}%")) |
                (Product.description.ilike(f"%{search}%"))
            )
        if low_stock:
            query = query.filter(Product.stock_quantity <= Product.low_stock_threshold)

        total = query.count()
        products = query.order_by(Product.created_at.desc()).offset(offset).limit(limit).all()
        return products, total

    @staticmethod
    def update_product(business_id, product_id, **kwargs):
        product = ProductService.get_product(business_id, product_id)
        allowed = {
            'name', 'description', 'sku', 'price', 'cost_price',
            'stock_quantity', 'low_stock_threshold', 'image_url',
            'status', 'category_id'
        }

        if 'category_id' in kwargs and kwargs['category_id']:
            cat = ProductCategory.query.filter_by(
                id=kwargs['category_id'], business_id=business_id
            ).first()
            if not cat:
                raise ResourceNotFoundError("Category not found for this business")

        for k, v in kwargs.items():
            if k in allowed and v is not None:
                setattr(product, k, v)

        db.session.commit()
        return product

    @staticmethod
    def delete_product(business_id, product_id):
        product = ProductService.get_product(business_id, product_id)
        db.session.delete(product)
        db.session.commit()
        return True

    @staticmethod
    def adjust_stock(business_id, product_id, delta):
        product = ProductService.get_product(business_id, product_id)
        new_quantity = product.stock_quantity + delta
        if new_quantity < 0:
            raise ValidationError(
                f"Insufficient stock for {product.name}. Available: {product.stock_quantity}, Requested deduction: {-delta}"
            )
        product.stock_quantity = new_quantity
        db.session.commit()
        return product
