from app.extensions import db
from app.whatsapp.models import BusinessWhatsAppAccount
from app.customers.services import CustomerService
from app.core.exceptions import ResourceNotFoundError, ValidationError, ConflictError


class WhatsAppAccountService:

    @staticmethod
    def connect_account(business_id, phone_number_id, display_phone_number,
                        waba_id, access_token=None, webhook_verify_token=None):
        if not phone_number_id or not display_phone_number or not waba_id:
            raise ValidationError("phone_number_id, display_phone_number, and waba_id are required")

        # Check if phone_number_id is taken by another business
        existing = BusinessWhatsAppAccount.query.filter_by(phone_number_id=phone_number_id).first()
        if existing and existing.business_id != business_id:
            raise ConflictError(f"WhatsApp Phone Number ID '{phone_number_id}' is already linked to another business")

        account = BusinessWhatsAppAccount.query.filter_by(business_id=business_id).first()
        if not account:
            account = BusinessWhatsAppAccount(
                business_id=business_id,
                phone_number_id=phone_number_id,
                display_phone_number=display_phone_number,
                waba_id=waba_id,
                access_token_encrypted=access_token,
                webhook_verify_token=webhook_verify_token,
                status='CONNECTED'
            )
            db.session.add(account)
        else:
            account.phone_number_id = phone_number_id
            account.display_phone_number = display_phone_number
            account.waba_id = waba_id
            if access_token:
                account.access_token_encrypted = access_token
            if webhook_verify_token:
                account.webhook_verify_token = webhook_verify_token
            account.status = 'CONNECTED'

        db.session.commit()
        return account

    @staticmethod
    def get_account(business_id):
        return BusinessWhatsAppAccount.query.filter_by(business_id=business_id).first()

    @staticmethod
    def disconnect_account(business_id):
        account = WhatsAppAccountService.get_account(business_id)
        if not account:
            raise ResourceNotFoundError("No WhatsApp account linked to this business")
        account.status = 'DISCONNECTED'
        db.session.commit()
        return account


class WhatsAppRouter:

    @staticmethod
    def extract_phone_number_id(payload):
        """Extracts destination phone_number_id from Meta webhook payload."""
        try:
            entries = payload.get('entry', [])
            if not entries:
                return None
            changes = entries[0].get('changes', [])
            if not changes:
                return None
            return changes[0].get('value', {}).get('metadata', {}).get('phone_number_id')
        except (IndexError, AttributeError, KeyError):
            return None

    @staticmethod
    def extract_messages(payload):
        """Extracts list of incoming messages from Meta webhook payload."""
        try:
            entries = payload.get('entry', [])
            if not entries:
                return []
            changes = entries[0].get('changes', [])
            if not changes:
                return []
            value = changes[0].get('value', {})
            return value.get('messages', [])
        except (IndexError, AttributeError, KeyError):
            return []

    @staticmethod
    def extract_contacts(payload):
        """Extracts contacts profile names from Meta webhook payload."""
        try:
            entries = payload.get('entry', [])
            if not entries:
                return {}
            changes = entries[0].get('changes', [])
            if not changes:
                return {}
            value = changes[0].get('value', {})
            contacts = value.get('contacts', [])
            return {c.get('wa_id'): c.get('profile', {}).get('name') for c in contacts if c.get('wa_id')}
        except (IndexError, AttributeError, KeyError):
            return {}

    @classmethod
    def handle_incoming_event(cls, payload):
        """
        Resolves the business by phone_number_id, ensures tenant customer record exists,
        and returns parsed event metadata scoped to business_id.
        """
        phone_number_id = cls.extract_phone_number_id(payload)
        if not phone_number_id:
            return {'status': 'ignored', 'reason': 'no_phone_number_id'}

        account = BusinessWhatsAppAccount.query.filter_by(
            phone_number_id=phone_number_id,
            status='CONNECTED'
        ).first()

        if not account:
            return {'status': 'unresolved_tenant', 'phone_number_id': phone_number_id}

        business_id = account.business_id
        messages = cls.extract_messages(payload)
        contacts = cls.extract_contacts(payload)

        processed = []
        for msg in messages:
            from_phone = msg.get('from')
            if not from_phone:
                continue

            customer_name = contacts.get(from_phone)
            # Ensure isolated customer profile exists for this business
            customer = CustomerService.get_or_create_by_phone(
                business_id=business_id,
                phone=from_phone,
                name=customer_name
            )

            msg_type = msg.get('type')
            text_body = msg.get('text', {}).get('body') if msg_type == 'text' else None

            processed.append({
                'message_id': msg.get('id'),
                'from_phone': from_phone,
                'customer_id': customer.id,
                'type': msg_type,
                'text': text_body,
                'timestamp': msg.get('timestamp')
            })

        return {
            'status': 'processed',
            'business_id': business_id,
            'waba_account_id': account.id,
            'messages': processed
        }
