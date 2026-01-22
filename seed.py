from app import app
from models import db, User
import bcrypt

with app.app_context():
    User.query.delete()

    password = bcrypt.hashpw(
        b"admin123",
        bcrypt.gensalt()
    ).decode("utf-8")

    admin = User(
        username="admin",
        password_hash=password
    )

    db.session.add(admin)
    db.session.commit()

    print("Admin user created: admin / admin123")