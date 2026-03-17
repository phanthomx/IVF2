import os

class Config:
    DEBUG = True

    basedir = os.path.abspath(os.path.dirname(__file__))
    instance_folder = os.path.join(basedir, 'instance')

    if not os.path.exists(instance_folder):
        os.makedirs(instance_folder)
        print(f"Created instance directory at {instance_folder}")

    DATABASE_PATH = os.path.join(instance_folder, 'database.sqlite3')
    print(f"Database will be stored at: {DATABASE_PATH}")

    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DATABASE_PATH}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SECRET_KEY = os.getenv('SECRET_KEY', 'defaultsecretkey')
    SECURITY_PASSWORD_SALT = 'mysecuritypasswordsalt'

    # ✅ Disable CSRF — required for REST API (no browser forms)
    WTF_CSRF_ENABLED = False
    SECURITY_WTF_CSRF_ENABLED = False

    # ✅ Prevent Flask-Security from hijacking your /login route
    SECURITY_URL_PREFIX = '/flask-security'

    # ✅ Disable redirects — Flask-Security redirects to /login on 401, breaking APIs
    SECURITY_UNAUTHORIZED_CALLBACK = None

    # ✅ Token auth header — matches your CORS config
    SECURITY_TOKEN_AUTHENTICATION_HEADER = 'Authentication-Token'

    # ✅ Don't require confirmation email to login
    SECURITY_CONFIRMABLE = False

    # ✅ Return JSON not HTML for auth errors
    SECURITY_REDIRECT_BEHAVIOR = 'spa'

    CACHE_TYPE = 'redis'
    CACHE_DEFAULT_TIMEOUT = 30
    CACHE_REDIS_HOST = 'localhost'
    CACHE_REDIS_PORT = 6379
    CACHE_REDIS_DB = 0

    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'ivfclinic6@gmail.com'
    MAIL_PASSWORD = 'szrq uqxh ehbw pqge'
    MAIL_DEFAULT_SENDER = ('Ivy Clinic', 'ivfclinic6@gmail.com')