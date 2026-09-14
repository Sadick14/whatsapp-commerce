def test_business_creation_and_listing(client, auth_headers):
    headers_a = {'Authorization': auth_headers['owner_a_raw_token']}
    res = client.get('/api/v1/businesses', headers=headers_a)
    assert res.status_code == 200
    biz_list = res.get_json()['businesses']
    assert len(biz_list) >= 1
    assert any(b['slug'] == 'sadick-sneakers' for b in biz_list)


def test_business_creation_with_type_whatsapp_and_paypal(client, auth_headers):
    headers_a = {'Authorization': auth_headers['owner_a_raw_token']}
    payload = {
        'name': 'Gourmet Pizza Restaurant',
        'slug': 'gourmet-pizza',
        'business_type': 'RESTAURANT',
        'whatsapp_config': {
            'phone_number_id': '1000998877665544',
            'display_phone_number': '+233240001122',
            'waba_id': '99887766554433',
            'access_token': 'test_waba_token'
        },
        'paypal_config': {
            'provider': 'PAYPAL',
            'paypal_email': 'payments@gourmetpizza.com',
            'paypal_client_id': 'client_id_123',
            'paypal_client_secret': 'client_secret_xyz',
            'paypal_mode': 'sandbox'
        }
    }
    res = client.post('/api/v1/businesses', headers=headers_a, json=payload)
    assert res.status_code == 201
    data = res.get_json()['business']
    assert data['name'] == 'Gourmet Pizza Restaurant'
    assert data['business_type'] == 'RESTAURANT'
    assert data['capabilities']['modifiers'] is True
    assert data['capabilities']['scheduled_orders'] is True

    biz_id = data['id']
    headers_biz = {'Authorization': auth_headers['owner_a_raw_token'], 'X-Business-ID': biz_id}

    # Verify WhatsApp account connected
    wa_res = client.get('/api/v1/channels/whatsapp', headers=headers_biz)
    assert wa_res.status_code == 200
    wa_data = wa_res.get_json()['account']
    assert wa_data['phone_number_id'] == '1000998877665544'

    # Verify PayPal payment config
    pay_res = client.get('/api/v1/payments/config', headers=headers_biz)
    assert pay_res.status_code == 200
    pay_data = pay_res.get_json()['config']
    assert pay_data['provider'] == 'PAYPAL'
    assert pay_data['paypal_email'] == 'payments@gourmetpizza.com'
    assert pay_data['paypal_client_id'] == 'client_id_123'


def test_business_team_rbac(client, auth_headers, test_businesses):
    biz_a_id = test_businesses['biz_a_id']

    # Owner can add manager
    owner_headers = auth_headers['owner_a_biz_a']
    res = client.post(f'/api/v1/businesses/{biz_a_id}/members', headers=owner_headers, json={
        'email': 'owner_b@example.com',
        'role': 'MANAGER'
    })
    assert res.status_code == 201

    # Staff cannot add members (insufficient permissions)
    staff_headers = auth_headers['staff_a_biz_a']
    res_staff = client.post(f'/api/v1/businesses/{biz_a_id}/members', headers=staff_headers, json={
        'email': 'staff_a@example.com',
        'role': 'STAFF'
    })
    assert res_staff.status_code == 403

    # Staff cannot update business profile
    res_update = client.patch(f'/api/v1/businesses/{biz_a_id}', headers=staff_headers, json={
        'name': 'Hacked Name'
    })
    assert res_update.status_code == 403
