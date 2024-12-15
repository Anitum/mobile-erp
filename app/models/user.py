from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), nullable=False)  # 'admin', 'teacher', 'student'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def create_default_admin():
        admin = User.query.filter_by(username='alka').first()
        if not admin:
            admin = User(
                username='alka',
                email='admin@school.com',
                role='admin',
                first_name='Admin',
                last_name='User',
                is_active=True
            )
            admin.set_password('yolo@9117')
            db.session.add(admin)
            db.session.commit()
            print("Default admin created successfully!")
