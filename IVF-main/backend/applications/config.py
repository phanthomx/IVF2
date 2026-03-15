import os

class Config:
    DEBUG = True

    # Get the base directory of the current file
    basedir = os.path.abspath(os.path.dirname(__file__))

    # Set the instance folder path
    instance_folder = os.path.join(basedir, 'instance')

    # Make sure the instance folder exists
    if not os.path.exists(instance_folder):
        os.makedirs(instance_folder)
        print(f"Created instance directory at {instance_folder}")

    # Set the SQLite database URI to point to the instance folder
    DATABASE_PATH = os.path.join(instance_folder, 'database.sqlite3')
    print(f"Database will be stored at: {DATABASE_PATH}")

    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DATABASE_PATH}"

    # Disable modification tracking for performance
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Secret and security settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'defaultsecretkey')
    SECURITY_PASSWORD_SALT = 'mysecuritypasswordsalt'

    # Redis cache configuration
    CACHE_TYPE = 'redis'
    CACHE_DEFAULT_TIMEOUT = 30
    CACHE_REDIS_HOST = 'localhost'
    CACHE_REDIS_PORT = 6379
    CACHE_REDIS_DB = 0