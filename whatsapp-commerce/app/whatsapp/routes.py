from flask import Blueprint, request, jsonify, g
from app.whatsapp.services import WhatsAppAccountService
from app.core.permissions import require_tenant

whatsapp_bp = Blueprint('whatsapp', __name__, url_prefix='/api/v1/channels/whatsapp')


@whatsapp_bp.route('', methods=['GET'])
@require_tenant(min_role='STAFF')
def get_whatsapp_status():
    account = WhatsAppAccountService.get_account(g.business_id)
    return jsonify(account=account.to_dict() if account else None), 200


@whatsapp_bp.route('/connect', methods=['POST'])
@require_tenant(min_role='ADMIN')
def connect_whatsapp():
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
    account = WhatsAppAccountService.disconnect_account(g.business_id)
    return jsonify(account=account.to_dict(), message="WhatsApp account disconnected"), 200
