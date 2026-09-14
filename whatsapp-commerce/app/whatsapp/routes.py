from flask import Blueprint, request, jsonify, g
from app.whatsapp.services import WhatsAppAccountService
from app.core.permissions import require_tenant

whatsapp_bp = Blueprint('whatsapp', __name__, url_prefix='/api/v1/channels/whatsapp')


@whatsapp_bp.route('', methods=['GET'])
@require_tenant(min_role='STAFF')
def get_whatsapp_status():
    """
    Get WhatsApp Business Account Integration Status
    ---
    tags:
      - WhatsApp Integration
    security:
      - Bearer: []
    parameters:
      - name: X-Business-ID
        in: header
        type: string
        required: true
    responses:
      200:
        description: WhatsApp integration account status
    """
    account = WhatsAppAccountService.get_account(g.business_id)
    return jsonify(account=account.to_dict() if account else None), 200


@whatsapp_bp.route('/connect', methods=['POST'])
@require_tenant(min_role='ADMIN')
def connect_whatsapp():
    """
    Connect / Configure WhatsApp Cloud API Settings
    ---
    tags:
      - WhatsApp Integration
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
            - phone_number_id
            - display_phone_number
            - access_token
          properties:
            phone_number_id:
              type: string
            display_phone_number:
              type: string
            waba_id:
              type: string
            access_token:
              type: string
            webhook_verify_token:
              type: string
    responses:
      200:
        description: WhatsApp account connected
    """
    data = request.get_json() or {}
    account = WhatsAppAccountService.connect_account(
        business_id=g.business_id,
        phone_number_id=data.get('phone_number_id'),
        display_phone_number=data.get('display_phone_number'),
        waba_id=data.get('waba_id'),
        access_token=data.get('access_token'),
        webhook_verify_token=data.get('webhook_verify_token')
    )
    return jsonify(account=account.to_dict()), 200


@whatsapp_bp.route('/disconnect', methods=['POST'])
@require_tenant(min_role='ADMIN')
def disconnect_whatsapp():
    """
    Disconnect WhatsApp Account Integration
    ---
    tags:
      - WhatsApp Integration
    security:
      - Bearer: []
    parameters:
      - name: X-Business-ID
        in: header
        type: string
        required: true
    responses:
      200:
        description: WhatsApp account disconnected
    """
    account = WhatsAppAccountService.disconnect_account(g.business_id)
    return jsonify(account=account.to_dict(), message="WhatsApp account disconnected"), 200
