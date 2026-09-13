def test_business_creation_and_listing(client, auth_headers):
    headers_a = {'Authorization': auth_headers['owner_a_raw_token']}
    res = client.get('/api/v1/businesses', headers=headers_a)
    assert res.status_code == 200
    biz_list = res.get_json()['businesses']
    assert len(biz_list) >= 1
    assert any(b['slug'] == 'sadick-sneakers' for b in biz_list)


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
