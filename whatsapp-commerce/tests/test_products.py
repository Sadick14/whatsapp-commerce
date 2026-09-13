def test_product_lifecycle_and_inventory(client, auth_headers):
    headers = auth_headers['owner_a_biz_a']

    # 1. Create Category
    res_cat = client.post('/api/v1/products/categories', headers=headers, json={
        'name': 'Footwear'
    })
    assert res_cat.status_code == 201
    cat_id = res_cat.get_json()['category']['id']

    # 2. Create Product
    res_prod = client.post('/api/v1/products', headers=headers, json={
        'name': 'Nike Air Max',
        'category_id': cat_id,
        'price': 350.00,
        'stock_quantity': 5,
        'low_stock_threshold': 3,
        'sku': 'NAM-001'
    })
    assert res_prod.status_code == 201
    prod = res_prod.get_json()['product']
    prod_id = prod['id']
    assert prod['category_name'] == 'Footwear'

    # 3. Adjust Stock
    res_stock = client.post(f'/api/v1/products/{prod_id}/stock', headers=headers, json={
        'delta': -3
    })
    assert res_stock.status_code == 200
    updated_prod = res_stock.get_json()['product']
    assert updated_prod['stock_quantity'] == 2
    assert updated_prod['is_low_stock'] is True

    # 4. Filter Low Stock
    res_low = client.get('/api/v1/products?low_stock=true', headers=headers)
    assert res_low.status_code == 200
    assert len(res_low.get_json()['products']) == 1

    # 5. Over-deduction fails
    res_fail = client.post(f'/api/v1/products/{prod_id}/stock', headers=headers, json={
        'delta': -10
    })
    assert res_fail.status_code == 400
