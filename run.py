from app import create_app, db
from app.models.user import User

app = create_app()

def init_db():
    with app.app_context():
        db.create_all()
        User.create_default_admin()

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host="0.0.0.0" )
