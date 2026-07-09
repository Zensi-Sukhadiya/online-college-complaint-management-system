import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "this_is_a_secret_key"

    database_url = os.environ.get("DATABASE_URL")

    if database_url:
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = database_url or "sqlite:///college.db"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = "app/static/uploads"

    MAX_CONTENT_LENGTH = 5 * 1024 * 1024