"""Configuración de la aplicación."""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuración base."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY')
    FAL_KEY = os.environ.get('FAL_KEY')
    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


class DevelopmentConfig(Config):
    """Configuración de desarrollo."""
    ENV = 'development'
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///melo.db'


class ProductionConfig(Config):
    """Configuración de producción."""
    ENV = 'production'
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///melo_prod.db'


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
