from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

login_manager.login_view = "login"
login_manager.login_message = "Please login first."

def create_app():
    app = Flask(__name__)

    from .config import Config
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    from . import models
    # from .routes import *
    

    @app.context_processor
    def inject_notifications():

        from flask_login import current_user
        from .models import Notification

        if current_user.is_authenticated:

            notifications = Notification.query.filter_by(
                user_id=current_user.id
            ).order_by(
                Notification.created_at.desc()
            ).limit(5).all()

            unread = Notification.query.filter_by(
                user_id=current_user.id,
                is_read=False
            ).count()

        else:
            notifications = []
            unread = 0

        return dict(
            notifications=notifications,
            unread_notifications=unread
        )
        
    from .routes import main
    app.register_blueprint(main)

    return app