def test_payment_flow_and_order_settlement(client, auth_headers):
    headers = auth_headers['owner_a_biz_a']

    # 1. Configure Gateway
    res_cfg = client.post('/api/v1/payments/config', headers=headers, json={
        'provider': 'PAYSTACK',
        'public_key': 'pk_test_123456',
        'secret_key': 'sk_test_654321',
        'subaccount_code': 'ACCT_xyz789'
    })
    assert res_cfg.status_code == 200
    cfg = res_cfg.get_json()['config']
    assert cfg['public_key'] == 'pk_test_123456'

    # 2. Create Product, Customer, and Order
    res_p = client.post('/api/v1/products', headers=headers, json={
        'name': 'Adidas Samba',
        'price': 150.00,
        'stock_quantity': 5
    })
    prod_id = res_p.get_json()['product']['id']

    res_c = client.post('/api/v1/customers', headers=headers, json={
        'phone': '+233249999999',
        'name': 'Yaw Boateng'
    })
    cust_id = res_c.get_json()['customer']['id']

    res_o = client.post('/api/v1/orders', headers=headers, json={
        'customer_id': cust_id,
        'items': [{'product_id': prod_id, 'quantity': 1}],
        'delivery_fee': 10.00
    })
    order_id = res_o.get_json()['order']['id']

    # 3. Record Payment
    res_pay = client.post('/api/v1/payments/record', headers=headers, json={
        'order_id': order_id,
        'amount': 160.00,
        'reference': 'PAY-REF-001',
        'provider': 'PAYSTACK',
        'payment_method': 'MOBILE_MONEY',
        'status': 'SUCCESS'
    })
    assert res_pay.status_code == 201
    payment = res_pay.get_json()['payment']
    assert payment['status'] == 'SUCCESS'

    # 4. Check Order is now PAID & CONFIRMED
    order_check = client.get(f'/api/v1/orders/{order_id}', headers=headers).get_json()['order']
    assert order_check['payment_status'] == 'PAID'
    assert order_check['status'] == 'CONFIRMED'
