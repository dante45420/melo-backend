"""Configuración de la aplicación."""
import os
from dotenv import load_dotenv

load_dotenv()


def _get_database_url():
    """Obtiene DATABASE_URL con soporte para Render (Internal/External)."""
    url = (
        os.environ.get('DATABASE_URL') or
        os.environ.get('DATABASE_INTERNAL_URL') or
        os.environ.get('INTERNAL_DATABASE_URL')
    )
    if not url or not isinstance(url, str) or not url.strip():
        return None
    url = url.strip()
    # SQLAlchemy 1.4+ requiere postgresql:// no postgres://
    if url.startswith('postgres://'):
        url = 'postgresql://' + url[11:]
    return url


class Config:
    """Configuración base."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY')
    FAL_KEY = os.environ.get('FAL_KEY')
    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
    # Token para proteger las APIs (debe coincidir con VITE_AUTH_TOKEN en frontend)
    API_SECRET = os.environ.get('API_SECRET') or os.environ.get('AUTH_TOKEN') or ''
    # Orígenes CORS permitidos (URL del frontend en Vercel, ej: https://melo.vercel.app)
    _cors = os.environ.get('CORS_ORIGINS', '') or ''
    CORS_ORIGINS = [x.strip().rstrip('/') for x in _cors.split(',') if x.strip()]
    # Fallback cuando CORS_ORIGINS está vacío
    if not CORS_ORIGINS:
        if os.environ.get('RENDER'):
            CORS_ORIGINS = ['https://melo-frontend.vercel.app']
        elif os.environ.get('FLASK_ENV') == 'development':
            CORS_ORIGINS = ['http://localhost:5173', 'http://127.0.0.1:5173']


class DevelopmentConfig(Config):
    """Configuración de desarrollo."""
    ENV = 'development'
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = _get_database_url() or 'sqlite:///melo.db'


class ProductionConfig(Config):
    """Configuración de producción."""
    ENV = 'production'
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = _get_database_url() or 'sqlite:///melo_prod.db'


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
