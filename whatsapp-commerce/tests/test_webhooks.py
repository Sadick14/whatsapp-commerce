def test_whatsapp_webhook_verification(client):
    res = client.get('/api/v1/webhooks/whatsapp?hub.mode=subscribe&hub.verify_token=dev-verify-token&hub.challenge=CHALLENGE_CODE_123')
    assert res.status_code == 200
    assert res.data.decode('utf-8') == 'CHALLENGE_CODE_123'

    res_invalid = client.get('/api/v1/webhooks/whatsapp?hub.mode=subscribe&hub.verify_token=wrong-token&hub.challenge=CHALLENGE_CODE_123')
    assert res_invalid.status_code == 403


def test_whatsapp_webhook_multi_tenant_routing(client, auth_headers, test_businesses):
    headers_a = auth_headers['owner_a_biz_a']
    headers_b = auth_headers['owner_b_biz_b']
    biz_a_id = test_businesses['biz_a_id']
    biz_b_id = test_businesses['biz_b_id']

    # 1. Connect Business A WhatsApp
    res_conn_a = client.post('/api/v1/channels/whatsapp/connect', headers=headers_a, json={
        'phone_number_id': 'PNID_BIZ_A_111',
        'display_phone_number': '+233241111111',
        'waba_id': 'WABA_A_111',
        'access_token': 'meta_token_a'
    })
    assert res_conn_a.status_code == 200

    # 2. Connect Business B WhatsApp
    res_conn_b = client.post('/api/v1/channels/whatsapp/connect', headers=headers_b, json={
        'phone_number_id': 'PNID_BIZ_B_222',
        'display_phone_number': '+233242222222',
        'waba_id': 'WABA_B_222',
        'access_token': 'meta_token_b'
    })
    assert res_conn_b.status_code == 200

    # 3. Webhook received targeting Business A
    meta_payload_a = {
        'entry': [{
            'changes': [{
                'value': {
                    'metadata': {'phone_number_id': 'PNID_BIZ_A_111'},
                    'contacts': [{'wa_id': '+233551234567', 'profile': {'name': 'Customer For A'}}],
                    'messages': [{
                        'id': 'wamid.HBgLMTIzNDU2Nw==',
                        'from': '+233551234567',
                        'type': 'text',
                        'text': {'body': 'Hi, I want to see your sneakers'},
                        'timestamp': '1700000000'
                    }]
                }
            }]
        }]
    }
    res_wh_a = client.post('/api/v1/webhooks/whatsapp', json=meta_payload_a)
    assert res_wh_a.status_code == 200
    data_a = res_wh_a.get_json()
    assert data_a['status'] == 'processed'
    assert data_a['business_id'] == biz_a_id
    assert len(data_a['messages']) == 1
    assert data_a['messages'][0]['text'] == 'Hi, I want to see your sneakers'

    # Customer record should exist under Business A
    cust_a = client.get(f"/api/v1/customers/{data_a['messages'][0]['customer_id']}", headers=headers_a)
    assert cust_a.status_code == 200
    assert cust_a.get_json()['customer']['name'] == 'Customer For A'

    # That customer ID should not be found in Business B
    cust_cross = client.get(f"/api/v1/customers/{data_a['messages'][0]['customer_id']}", headers=headers_b)
    assert cust_cross.status_code == 404

    # 4. Webhook received for unlinked phone_number_id
    meta_unlinked = {
        'entry': [{
            'changes': [{
                'value': {
                    'metadata': {'phone_number_id': 'UNLINKED_PHONE_ID'},
                    'messages': []
                }
            }]
        }]
    }
    res_unlinked = client.post('/api/v1/webhooks/whatsapp', json=meta_unlinked)
    assert res_unlinked.status_code == 200
    assert res_unlinked.get_json()['status'] == 'ignored'
