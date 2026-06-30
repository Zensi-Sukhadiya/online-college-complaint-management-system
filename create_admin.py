from werkzeug.security import generate_password_hash
from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():

    admin = User.query.filter_by(email="admin@gmail.com").first()

    if admin:
        print("Admin already exists!")

    else:
        admin = User(
            name="Administrator",
            email="admin@gmail.com",
            password=generate_password_hash("admin123"),
            role="admin",
            department="Administration",
            contact_number="9999999999"
        )

        db.session.add(admin)
        db.session.commit()

        print("Admin created successfully!")