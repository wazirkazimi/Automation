import os
from datetime import timedelta

class Config:
    """Base configuration"""
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Uploads
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    OUTPUT_FOLDER = os.getenv('OUTPUT_FOLDER', 'outputs')
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB max file size
    
    # Video processing
    VIDEO_TIMEOUT = 300  # 5 minutes for video encoding
    
    # Gunicorn
    WORKERS = int(os.getenv('WORKERS', 4))
    WORKER_CLASS = 'gevent'
    WORKER_CONNECTIONS = 1000
    
    # Job cleanup
    JOB_CLEANUP_INTERVAL = 3600  # Clean up old jobs every hour


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    ENV = 'development'


class ProductionConfig(Config):
    """Production configuration for Render/cloud deployment"""
    DEBUG = False
    TESTING = False
    ENV = 'production'
    
    def __init__(self):
        super().__init__()
        if not os.getenv('SECRET_KEY'):
            raise ValueError("SECRET_KEY environment variable must be set in production")
    
    SECRET_KEY = os.getenv('SECRET_KEY', 'production-secret-key-must-be-set')


class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    ENV = 'testing'
    UPLOAD_FOLDER = 'test_uploads'
    OUTPUT_FOLDER = 'test_outputs'


# Config selection
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(env=None):
    """Get configuration object based on environment"""
    if env is None:
        env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default'])
