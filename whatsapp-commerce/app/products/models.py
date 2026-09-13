from app.extensions import db
from app.core.base_model import gen_uuid, TimestampMixin, TenantMixin


class ProductCategory(db.Model, TimestampMixin, TenantMixin):
    __tablename__ = 'product_categories'

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), nullable=False)

    products = db.relationship('Product', back_populates='category', lazy='dynamic')

    __table_args__ = (
        db.UniqueConstraint('business_id', 'slug', name='uq_biz_category_slug'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'business_id': self.business_id,
            'name': self.name,
            'slug': self.slug,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Product(db.Model, TimestampMixin, TenantMixin):
    __tablename__ = 'products'

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    category_id = db.Column(
        db.String(36),
        db.ForeignKey('product_categories.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    sku = db.Column(db.String(100))
    price = db.Column(db.Numeric(10, 2), nullable=False)
    cost_price = db.Column(db.Numeric(10, 2), nullable=True)
    stock_quantity = db.Column(db.Integer, default=0, nullable=False)
    low_stock_threshold = db.Column(db.Integer, default=5, nullable=False)
    image_url = db.Column(db.Text)
    status = db.Column(db.String(20), default='ACTIVE', nullable=False)  # ACTIVE, INACTIVE, ARCHIVED

    category = db.relationship('ProductCategory', back_populates='products')

    __table_args__ = (
        db.Index('idx_products_biz_status', 'business_id', 'status'),
    )

    @property
    def is_low_stock(self):
        return self.stock_quantity <= self.low_stock_threshold

    def to_dict(self):
        return {
            'id': self.id,
            'business_id': self.business_id,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else None,
            'name': self.name,
            'description': self.description,
            'sku': self.sku,
            'price': float(self.price) if self.price is not None else 0.0,
            'cost_price': float(self.cost_price) if self.cost_price is not None else None,
            'stock_quantity': self.stock_quantity,
            'low_stock_threshold': self.low_stock_threshold,
            'is_low_stock': self.is_low_stock,
            'image_url': self.image_url,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
