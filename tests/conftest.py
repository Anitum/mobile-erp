import pytest
from app import create_app, db
from app.models.user import User
from flask import url_for


@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['UPLOAD_FOLDER'] = 'tests/uploads'
    app.config['SERVER_NAME'] = 'localhost'
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def init_database(app):
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        
        # Check if test user exists
        existing_user = User.query.filter_by(username='test_user').first()
        if not existing_user:
            test_user = User(
                username='test_user',
                email='test@example.com',
                role='teacher'
            )
            test_user.set_password('password123')
            try:
                db.session.add(test_user)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(f"Error creating test user: {e}")
        
        yield db
        
        # Only clean up the session, don't drop tables
        db.session.remove()

@pytest.fixture
def auth_teacher_client(app, client, init_database):
    with app.app_context():
        # Login the user
        client.post(url_for('auth.login'), data={
            'username': 'test_user',
            'password': 'password123',
            'remember_me': 'y'
        }, follow_redirects=True)
        
        # Return authenticated client
        return client