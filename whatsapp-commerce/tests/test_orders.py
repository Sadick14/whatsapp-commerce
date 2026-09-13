def test_order_creation_and_inventory_deduction(client, auth_headers):
    headers = auth_headers['owner_a_biz_a']

    # 1. Create Product with stock = 10
    res_p = client.post('/api/v1/products', headers=headers, json={
        'name': 'Puma Suede',
        'price': 200.00,
        'stock_quantity': 10
    })
    assert res_p.status_code == 201
    prod_id = res_p.get_json()['product']['id']

    # 2. Create Customer
    res_c = client.post('/api/v1/customers', headers=headers, json={
        'phone': '+233245555555',
        'name': 'Kwame Mensah',
        'default_delivery_address': 'East Legon, Accra'
    })
    assert res_c.status_code == 201
    cust_id = res_c.get_json()['customer']['id']

    # 3. Place Order for 3 units
    res_order = client.post('/api/v1/orders', headers=headers, json={
        'customer_id': cust_id,
        'items': [{'product_id': prod_id, 'quantity': 3}],
        'delivery_fee': 20.00,
        'channel': 'WHATSAPP'
    })
    assert res_order.status_code == 201
    order = res_order.get_json()['order']
    order_id = order['id']
    assert order['subtotal'] == 600.00
    assert order['total_amount'] == 620.00
    assert order['status'] == 'PENDING'
    assert order['payment_status'] == 'UNPAID'
    assert len(order['items']) == 1

    # 4. Verify Product stock is now 7
    prod_check = client.get(f'/api/v1/products/{prod_id}', headers=headers).get_json()['product']
    assert prod_check['stock_quantity'] == 7

    # 5. Transition status: PENDING -> CONFIRMED
    res_conf = client.patch(f'/api/v1/orders/{order_id}/status', headers=headers, json={
        'status': 'CONFIRMED'
    })
    assert res_conf.status_code == 200
    assert res_conf.get_json()['order']['status'] == 'CONFIRMED'

    # 6. Invalid transition: CONFIRMED -> DELIVERED (must go through PROCESSING / SHIPPED)
    res_inv = client.patch(f'/api/v1/orders/{order_id}/status', headers=headers, json={
        'status': 'DELIVERED'
    })
    assert res_inv.status_code == 409

    # 7. Cancel Order and verify stock restored to 10
    res_cancel = client.post(f'/api/v1/orders/{order_id}/cancel', headers=headers, json={
        'reason': 'Customer changed mind'
    })
    assert res_cancel.status_code == 200
    assert res_cancel.get_json()['order']['status'] == 'CANCELLED'

    prod_restored = client.get(f'/api/v1/products/{prod_id}', headers=headers).get_json()['product']
    assert prod_restored['stock_quantity'] == 10
