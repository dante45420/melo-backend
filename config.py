import os
from dotenv import load_dotenv

load_dotenv()


def get_database_uri():
    uri = os.getenv("DATABASE_URL")
    if uri and uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)
    return uri or "sqlite:///melo.db"


def get_admin_credentials():
    user = os.getenv("ADMIN_USER")
    password = os.getenv("ADMIN_PASSWORD")
    if not user or not password:
        raise ValueError("ADMIN_USER y ADMIN_PASSWORD deben estar en .env")
    return user, password
