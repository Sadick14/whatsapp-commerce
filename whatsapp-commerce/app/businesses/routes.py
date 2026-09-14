from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.businesses.services import BusinessService
from app.core.permissions import require_tenant

businesses_bp = Blueprint('businesses', __name__, url_prefix='/api/v1/businesses')


@businesses_bp.route('', methods=['POST'])
@jwt_required()
def create_business():
    """
    Create a new business workspace
    ---
    tags:
      - Businesses
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - name
            - slug
          properties:
            name:
              type: string
              example: Acme Mart
            slug:
              type: string
              example: acme-mart
            currency:
              type: string
              example: GHS
            phone:
              type: string
              example: "+233201112223"
            email:
              type: string
              example: contact@acmemart.com
            address:
              type: string
              example: "123 Ring Road, Accra"
            logo_url:
              type: string
              example: "https://example.com/logo.png"
    responses:
      201:
        description: Business created successfully
      401:
        description: Unauthorized
    """
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    business = BusinessService.create_business(
        owner_id=user_id,
        name=data.get('name'),
        slug=data.get('slug'),
        currency=data.get('currency', 'GHS'),
        phone=data.get('phone'),
        email=data.get('email'),
        address=data.get('address'),
        logo_url=data.get('logo_url')
    )
    return jsonify(business=business.to_dict()), 201


@businesses_bp.route('', methods=['GET'])
@jwt_required()
def list_my_businesses():
    """
    List user's business workspaces
    ---
    tags:
      - Businesses
    security:
      - Bearer: []
    responses:
      200:
        description: List of business memberships
    """
    user_id = get_jwt_identity()
    businesses = BusinessService.list_user_businesses(user_id)
    return jsonify(businesses=businesses), 200


@businesses_bp.route('/<business_id>', methods=['GET'])
@require_tenant(min_role='STAFF')
def get_business_details(business_id):
    """
    Get details for a specific business workspace
    ---
    tags:
      - Businesses
    security:
      - Bearer: []
    parameters:
      - name: business_id
        in: path
        type: string
        required: true
      - name: X-Business-ID
        in: header
        type: string
        required: false
    responses:
      200:
        description: Business details
      403:
        description: Insufficient permission or not a workspace member
    """
    return jsonify(business=g.business.to_dict(), my_role=g.member_role), 200


@businesses_bp.route('/<business_id>', methods=['PATCH'])
@require_tenant(min_role='ADMIN')
def update_business_profile(business_id):
    """
    Update business details
    ---
    tags:
      - Businesses
    security:
      - Bearer: []
    parameters:
      - name: business_id
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
            currency:
              type: string
            phone:
              type: string
            email:
              type: string
            address:
              type: string
            logo_url:
              type: string
    responses:
      200:
        description: Updated business profile
    """
    data = request.get_json() or {}
    updated = BusinessService.update_business(business_id, **data)
    return jsonify(business=updated.to_dict()), 200


@businesses_bp.route('/<business_id>/members', methods=['GET'])
@require_tenant(min_role='MANAGER')
def list_members(business_id):
    """
    List team members of a business
    ---
    tags:
      - Businesses
    security:
      - Bearer: []
    parameters:
      - name: business_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: List of team members
    """
    members = BusinessService.list_members(business_id)
    return jsonify(members=[m.to_dict() for m in members]), 200


@businesses_bp.route('/<business_id>/members', methods=['POST'])
@require_tenant(min_role='ADMIN')
def add_member(business_id):
    """
    Add/invite a team member to a business
    ---
    tags:
      - Businesses
    security:
      - Bearer: []
    parameters:
      - name: business_id
        in: path
        type: string
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - email
          properties:
            email:
              type: string
              example: staff@example.com
            role:
              type: string
              enum: [ADMIN, MANAGER, STAFF]
              default: STAFF
    responses:
      201:
        description: Team member added
    """
    data = request.get_json() or {}
    member = BusinessService.add_member(
        business_id=business_id,
        user_email=data.get('email'),
        role=data.get('role', 'STAFF'),
        invited_by=g.user_id
    )
    return jsonify(member=member.to_dict()), 201


@businesses_bp.route('/<business_id>/members/<user_id>', methods=['DELETE'])
@require_tenant(min_role='ADMIN')
def remove_member(business_id, user_id):
    """
    Remove team member from a business
    ---
    tags:
      - Businesses
    security:
      - Bearer: []
    parameters:
      - name: business_id
        in: path
        type: string
        required: true
      - name: user_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Member removed
    """
    BusinessService.remove_member(business_id, user_id)
    return jsonify(message="Member removed successfully"), 200
