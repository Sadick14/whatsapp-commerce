from flask import Blueprint, request, jsonify, g
from app.products.services import ProductService
from app.core.permissions import require_tenant

products_bp = Blueprint('products', __name__, url_prefix='/api/v1/products')


@products_bp.route('/categories', methods=['GET'])
@require_tenant(min_role='STAFF')
def list_categories():
    """
    List Product Categories
    ---
    tags:
      - Products
    security:
      - Bearer: []
    parameters:
      - name: X-Business-ID
        in: header
        type: string
        required: true
    responses:
      200:
        description: List of categories
    """
    categories = ProductService.list_categories(g.business_id)
    return jsonify(categories=[c.to_dict() for c in categories]), 200


@products_bp.route('/categories', methods=['POST'])
@require_tenant(min_role='MANAGER')
def create_category():
    """
    Create Product Category
    ---
    tags:
      - Products
    security:
      - Bearer: []
    parameters:
      - name: X-Business-ID
        in: header
        type: string
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - name
          properties:
            name:
              type: string
              example: Electronics
            slug:
              type: string
              example: electronics
    responses:
      201:
        description: Category created
    """
    data = request.get_json() or {}
    category = ProductService.create_category(
        business_id=g.business_id,
        name=data.get('name'),
        slug=data.get('slug')
    )
    return jsonify(category=category.to_dict()), 201


@products_bp.route('', methods=['GET'])
@require_tenant(min_role='STAFF')
def list_products():
    """
    List Products
    ---
    tags:
      - Products
    security:
      - Bearer: []
    parameters:
      - name: X-Business-ID
        in: header
        type: string
        required: true
      - name: category_id
        in: query
        type: string
      - name: status
        in: query
        type: string
      - name: search
        in: query
        type: string
      - name: low_stock
        in: query
        type: boolean
      - name: limit
        in: query
        type: integer
        default: 50
      - name: offset
        in: query
        type: integer
        default: 0
    responses:
      200:
        description: List of products with pagination total
    """
    category_id = request.args.get('category_id')
    status = request.args.get('status')
    search = request.args.get('search')
    low_stock = request.args.get('low_stock', '').lower() in ('true', '1')
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))

    products, total = ProductService.list_products(
        business_id=g.business_id,
        category_id=category_id,
        status=status,
        search=search,
        low_stock=low_stock,
        limit=limit,
        offset=offset
    )
    return jsonify(
        products=[p.to_dict() for p in products],
        total=total,
        limit=limit,
        offset=offset
    ), 200


@products_bp.route('', methods=['POST'])
@require_tenant(min_role='MANAGER')
def create_product():
    """
    Create Product
    ---
    tags:
      - Products
    security:
      - Bearer: []
    parameters:
      - name: X-Business-ID
        in: header
        type: string
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - name
            - price
          properties:
            name:
              type: string
              example: Wireless Headphones
            price:
              type: number
              example: 150.00
            category_id:
              type: string
            description:
              type: string
            sku:
              type: string
            cost_price:
              type: number
            stock_quantity:
              type: integer
              default: 0
            low_stock_threshold:
              type: integer
              default: 5
            image_url:
              type: string
            status:
              type: string
              enum: [ACTIVE, INACTIVE, ARCHIVED]
              default: ACTIVE
    responses:
      201:
        description: Product created
    """
    data = request.get_json() or {}
    product = ProductService.create_product(
        business_id=g.business_id,
        name=data.get('name'),
        price=data.get('price'),
        category_id=data.get('category_id'),
        description=data.get('description'),
        sku=data.get('sku'),
        cost_price=data.get('cost_price'),
        stock_quantity=data.get('stock_quantity', 0),
        low_stock_threshold=data.get('low_stock_threshold', 5),
        image_url=data.get('image_url'),
        status=data.get('status', 'ACTIVE')
    )
    return jsonify(product=product.to_dict()), 201


@products_bp.route('/<product_id>', methods=['GET'])
@require_tenant(min_role='STAFF')
def get_product(product_id):
    """
    Get Product Details
    ---
    tags:
      - Products
    security:
      - Bearer: []
    parameters:
      - name: X-Business-ID
        in: header
        type: string
        required: true
      - name: product_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Product details
    """
    product = ProductService.get_product(g.business_id, product_id)
    return jsonify(product=product.to_dict()), 200


@products_bp.route('/<product_id>', methods=['PATCH'])
@require_tenant(min_role='MANAGER')
def update_product(product_id):
    """
    Update Product Details
    ---
    tags:
      - Products
    security:
      - Bearer: []
    parameters:
      - name: X-Business-ID
        in: header
        type: string
        required: true
      - name: product_id
        in: path
        type: string
        required: true
      - in: body
        name: body
        schema:
          type: object
          properties:
            name:
              type: string
            price:
              type: number
            category_id:
              type: string
            description:
              type: string
            sku:
              type: string
            cost_price:
              type: number
            stock_quantity:
              type: integer
            low_stock_threshold:
              type: integer
            image_url:
              type: string
            status:
              type: string
    responses:
      200:
        description: Updated product details
    """
    data = request.get_json() or {}
    updated = ProductService.update_product(g.business_id, product_id, **data)
    return jsonify(product=updated.to_dict()), 200


@products_bp.route('/<product_id>', methods=['DELETE'])
@require_tenant(min_role='MANAGER')
def delete_product(product_id):
    """
    Delete Product
    ---
    tags:
      - Products
    security:
      - Bearer: []
    parameters:
      - name: X-Business-ID
        in: header
        type: string
        required: true
      - name: product_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Product deleted
    """
    ProductService.delete_product(g.business_id, product_id)
    return jsonify(message="Product deleted successfully"), 200


@products_bp.route('/<product_id>/stock', methods=['POST'])
@require_tenant(min_role='STAFF')
def adjust_stock(product_id):
    """
    Adjust Product Stock Quantity
    ---
    tags:
      - Products
    security:
      - Bearer: []
    parameters:
      - name: X-Business-ID
        in: header
        type: string
        required: true
      - name: product_id
        in: path
        type: string
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - delta
          properties:
            delta:
              type: integer
              example: 10
    responses:
      200:
        description: Updated stock quantity
      400:
        description: Missing delta parameter
    """
    data = request.get_json() or {}
    delta = data.get('delta')
    if delta is None:
        return jsonify(error="delta integer required"), 400
    updated = ProductService.adjust_stock(g.business_id, product_id, int(delta))
    return jsonify(product=updated.to_dict()), 200
