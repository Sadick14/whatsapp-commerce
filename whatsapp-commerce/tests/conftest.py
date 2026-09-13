import pytest
from app import create_app
from app.extensions import db as _db
from app.auth.services import AuthService
from app.businesses.services import BusinessService
from flask_jwt_extended import create_access_token


@pytest.fixture(scope='session')
def app():
    app = create_app('testing')
    return app


@pytest.fixture(autouse=True)
def db_session(app):
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def test_data(app, db_session):
    with app.app_context():
        user_a = AuthService.register("owner_a@example.com", "Password123!", "Alice Owner", "+233240000001")
        user_b = AuthService.register("owner_b@example.com", "Password123!", "Bob Owner", "+233240000002")
        staff_a = AuthService.register("staff_a@example.com", "Password123!", "Sam Staff", "+233240000003")

        user_a_id = user_a.id
        user_b_id = user_b.id
        staff_a_id = staff_a.id

        biz_a = BusinessService.create_business(
            owner_id=user_a_id,
            name="Sadick Sneakers",
            slug="sadick-sneakers",
            currency="GHS",
            phone="+233241111111"
        )
        biz_b = BusinessService.create_business(
            owner_id=user_b_id,
            name="Ama Beauty",
            slug="ama-beauty",
            currency="GHS",
            phone="+233242222222"
        )
        BusinessService.add_member(
            business_id=biz_a.id,
            user_email="staff_a@example.com",
            role="STAFF",
            invited_by=user_a_id
        )

        biz_a_id = biz_a.id
        biz_b_id = biz_b.id

        token_a = create_access_token(identity=user_a_id)
        token_b = create_access_token(identity=user_b_id)
        token_staff = create_access_token(identity=staff_a_id)

        return {
            'users': {
                'owner_a_id': user_a_id,
                'owner_b_id': user_b_id,
                'staff_a_id': staff_a_id
            },
            'businesses': {
                'biz_a_id': biz_a_id,
                'biz_b_id': biz_b_id
            },
            'auth_headers': {
                'owner_a_biz_a': {
                    'Authorization': f'Bearer {token_a}',
                    'X-Business-ID': biz_a_id
                },
                'owner_b_biz_b': {
                    'Authorization': f'Bearer {token_b}',
                    'X-Business-ID': biz_b_id
                },
                'staff_a_biz_a': {
                    'Authorization': f'Bearer {token_staff}',
                    'X-Business-ID': biz_a_id
                },
                'owner_a_raw_token': f'Bearer {token_a}',
                'owner_b_raw_token': f'Bearer {token_b}',
                'staff_a_raw_token': f'Bearer {token_staff}'
            }
        }


@pytest.fixture
def auth_headers(test_data):
    return test_data['auth_headers']


@pytest.fixture
def test_businesses(test_data):
    return {
        'biz_a_id': test_data['businesses']['biz_a_id'],
        'biz_b_id': test_data['businesses']['biz_b_id']
    }


@pytest.fixture
def test_users(test_data):
    return test_data['users']
