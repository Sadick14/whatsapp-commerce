def test_cross_tenant_workspace_access_denied(client, auth_headers, test_businesses):
    biz_b_id = test_businesses['biz_b_id']
    # Owner A tries to access Business B by spoofing X-Business-ID
    malicious_headers = {
        'Authorization': auth_headers['owner_a_raw_token'],
        'X-Business-ID': biz_b_id
    }
    res = client.get(f'/api/v1/businesses/{biz_b_id}', headers=malicious_headers)
    assert res.status_code == 403
    assert "Access denied" in res.get_json()['error']


def test_products_strict_tenant_isolation(client, auth_headers):
    headers_a = auth_headers['owner_a_biz_a']
    headers_b = auth_headers['owner_b_biz_b']

    # 1. Business A creates Product A
    res_a = client.post('/api/v1/products', headers=headers_a, json={
        'name': 'Air Jordan 1',
        'price': 450.00,
        'stock_quantity': 10
    })
    assert res_a.status_code == 201
    prod_a_id = res_a.get_json()['product']['id']

    # 2. Business B creates Product B
    res_b = client.post('/api/v1/products', headers=headers_b, json={
        'name': 'Shea Butter Cream',
        'price': 80.00,
        'stock_quantity': 50
    })
    assert res_b.status_code == 201
    prod_b_id = res_b.get_json()['product']['id']

    # 3. Business A lists products - should ONLY see Product A
    list_a = client.get('/api/v1/products', headers=headers_a)
    assert list_a.status_code == 200
    items_a = list_a.get_json()['products']
    assert len(items_a) == 1
    assert items_a[0]['name'] == 'Air Jordan 1'

    # 4. Business B lists products - should ONLY see Product B
    list_b = client.get('/api/v1/products', headers=headers_b)
    assert list_b.status_code == 200
    items_b = list_b.get_json()['products']
    assert len(items_b) == 1
    assert items_b[0]['name'] == 'Shea Butter Cream'

    # 5. Business A tries to GET Product B by ID - must return 404 (not found in Business A)
    cross_get = client.get(f'/api/v1/products/{prod_b_id}', headers=headers_a)
    assert cross_get.status_code == 404


def test_customer_isolation_same_phone_different_businesses(client, auth_headers):
    headers_a = auth_headers['owner_a_biz_a']
    headers_b = auth_headers['owner_b_biz_b']
    phone = "+233241234567"

    # Customer buys from Business A
    res_a = client.post('/api/v1/customers', headers=headers_a, json={
        'phone': phone,
        'name': 'Kofi SneakerFan'
    })
    assert res_a.status_code == 201
    cust_a = res_a.get_json()['customer']
    assert cust_a['name'] == 'Kofi SneakerFan'

    # Customer buys from Business B
    res_b = client.post('/api/v1/customers', headers=headers_b, json={
        'phone': phone,
        'name': 'Kofi BeautyFan'
    })
    assert res_b.status_code == 201
    cust_b = res_b.get_json()['customer']
    assert cust_b['name'] == 'Kofi BeautyFan'

    # Ensure different IDs and isolated profiles
    assert cust_a['id'] != cust_b['id']

    # List customers for Business A
    list_a = client.get('/api/v1/customers', headers=headers_a).get_json()['customers']
    assert len(list_a) == 1
    assert list_a[0]['name'] == 'Kofi SneakerFan'

    # List customers for Business B
    list_b = client.get('/api/v1/customers', headers=headers_b).get_json()['customers']
    assert len(list_b) == 1
    assert list_b[0]['name'] == 'Kofi BeautyFan'
