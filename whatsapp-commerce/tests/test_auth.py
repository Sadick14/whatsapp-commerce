def test_user_registration_and_login(client):
    # Register
    res = client.post('/api/v1/auth/register', json={
        'email': 'newowner@test.com',
        'password': 'SecretPassword123!',
        'full_name': 'New Owner',
        'phone': '+233201234567'
    })
    assert res.status_code == 201
    data = res.get_json()
    assert 'access_token' in data
    assert data['user']['email'] == 'newowner@test.com'

    # Duplicate registration error
    res_dup = client.post('/api/v1/auth/register', json={
        'email': 'newowner@test.com',
        'password': 'AnotherPassword!'
    })
    assert res_dup.status_code == 409

    # Login
    res_login = client.post('/api/v1/auth/login', json={
        'email': 'newowner@test.com',
        'password': 'SecretPassword123!'
    })
    assert res_login.status_code == 200
    token = res_login.get_json()['access_token']

    # Get Me profile
    res_me = client.get('/api/v1/auth/me', headers={'Authorization': f'Bearer {token}'})
    assert res_me.status_code == 200
    assert res_me.get_json()['user']['email'] == 'newowner@test.com'
