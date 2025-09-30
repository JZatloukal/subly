"""
Konfigurace aplikace Subly
Obsahuje nastavení pro vývoj, testování a produkci
"""

import os
from datetime import timedelta

class Config:
    """Základní konfigurační třída"""
    # Bezpečnostní klíč - v produkci MUSÍ být nastaven přes environment variable
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Databáze - v produkci použít PostgreSQL
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///database.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,  # Automatické testování připojení
        'pool_recycle': 300,    # Recyklace připojení každých 5 minut
    }
    
    # Adresář pro upload souborů
    UPLOAD_FOLDER = 'uploads'
    
    # Konfigurace session
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = False  # V produkci s HTTPS nastavit na True
    SESSION_COOKIE_HTTPONLY = True
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)
    
    # Konfigurace e-mailu (pro budoucí notifikace)
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # Nastavení aplikace
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # Maximální velikost souboru 16MB
    UPLOAD_EXTENSIONS = ['.csv']  # Povolené přípony souborů
    
    # Bezpečnostní nastavení
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hodina

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = False  # Vypnuto pro rychlejší odezvu
    SQLALCHEMY_DATABASE_URI = 'sqlite:///dev_database.db'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    
    def __init__(self):
        # Ensure secret key is set in production
        if not os.environ.get('SECRET_KEY'):
            raise ValueError("SECRET_KEY environment variable must be set in production")
        
        # Ensure database URL is set in production
        if not os.environ.get('DATABASE_URL'):
            raise ValueError("DATABASE_URL environment variable must be set in production")
        
        # Set PostgreSQL database URI
        self.SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

class PostgreSQLConfig(Config):
    """PostgreSQL configuration for Railway deployment"""
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    
    def __init__(self):
        # Ensure required environment variables are set
        if not os.environ.get('SECRET_KEY'):
            raise ValueError("SECRET_KEY environment variable must be set")
        
        if not os.environ.get('DATABASE_URL'):
            raise ValueError("DATABASE_URL environment variable must be set")
        
        # Set PostgreSQL database URI
        self.SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'postgresql': PostgreSQLConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
