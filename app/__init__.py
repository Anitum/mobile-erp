from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    from app.models.user import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from app.blueprints.auth import auth
    from app.blueprints.admin import admin
    from app.blueprints.teacher import teacher
    from app.blueprints.student import student

    app.register_blueprint(auth)
    app.register_blueprint(admin)
    app.register_blueprint(teacher)
    app.register_blueprint(student)

    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))

    return app
