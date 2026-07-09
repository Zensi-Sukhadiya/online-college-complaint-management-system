import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "this_is_a_secret_key"

    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or "sqlite:///college.db"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = "app/static/uploads"
    
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB