import os
from flask import Blueprint, request, jsonify, current_app
from app.whatsapp.services import WhatsAppRouter

whatsapp_webhook_bp = Blueprint('whatsapp_webhook', __name__, url_prefix='/api/v1/webhooks/whatsapp')


@whatsapp_webhook_bp.route('', methods=['GET'])
def verify_webhook():
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

    expected_token = current_app.config.get('WHATSAPP_VERIFY_TOKEN', 'dev-verify-token')

    if mode == 'subscribe' and token == expected_token:
        return challenge, 200
    return jsonify(error="Verification token mismatch"), 403


@whatsapp_webhook_bp.route('', methods=['POST'])
def receive_webhook():
    payload = request.get_json() or {}
    result = WhatsAppRouter.handle_incoming_event(payload)

    if result.get('status') == 'unresolved_tenant':
        return jsonify(status="ignored", reason="Unregistered WhatsApp receiver"), 200

    return jsonify(result), 200
