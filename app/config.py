import os
from dotenv import load_dotenv
import app.services.access
load_dotenv()

# default key if missing
default_key = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


def strippers(data: str) -> list[str]:
    if data:
        return [url.strip() for url in data.split(',')]
    return ["http://localhost:5173"]

class Config:
    BACKEND_ADDRESS = os.environ.get("BACKEND_ADDRESS", "0.0.0.0")
    BACKEND_PORT = os.environ.get("BACKEND_PORT", 5000)
    FLASK_ENVIRONMENT = os.environ.get("FLASK_ENVIRONMENT", 'development')

    # flask server
    FLASK_SECRET_KEY = os.environ.get("SECRET_NI_FLASK", default_key)
    JWT_SECRET_KEY = os.environ.get("SECRET_NI_JWT", default_key)

    # mail server credentials
    MAIL_SERVER_ADDRESS = os.environ.get("MAIL_SERVER_ADDRESS", "smpt.changeme.com")
    MAIL_SERVER_PORT = os.environ.get("MAIL_SERVER_PORT", "123")
    MAIL_ADDRESS = os.environ.get("MAIL_ADDRESS", "changeme@example.com")
    MAIL_PASSKEY =  os.environ.get("MAIL_PASSKEY", "XXX XXXX XXX")

    # default admin email
    ROOT_ADMIN_USERNAME = os.environ.get("ROOT_ADMIN_USERNAME", "root")
    ROOT_ADMIN_FIRST_NAME = os.environ.get("ROOT_ADMIN_FIRST_NAME", "Walter")
    ROOT_ADMIN_MIDDLE_NAME = os.environ.get("ROOT_ADMIN_MIDDLE_NAME", "Hartwell")
    ROOT_ADMIN_LAST_NAME = os.environ.get("ROOT_ADMIN_LAST_NAME", "White")
    ROOT_ADMIN_EMAIL = os.environ.get("ROOT_ADMIN_EMAIL", "example@gmail.com")
    ROOT_ADMIN_PASSWORD = os.environ.get("ROOT_ADMIN_PASSWORD", "changeme123")

    # database
    MYSQL_POOL_SIZE = os.environ.get("MYSQL_POOL_SIZE", 10)
    MYSQL_HOST = os.environ.get("MYSQL_HOST", "localhost")
    MYSQL_PORT = os.environ.get("MYSQL_PORT", "3306")
    MYSQL_DB = os.environ.get("MYSQL_DATABASE", "system_database")
    MYSQL_USER = os.environ.get("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "changeme123")

    # web client
    WEB_CLIENT_HOSTS = strippers(os.environ.get("WEB_CLIENT_HOSTS"))

    access_levels = app.services.access.access_level_lookup()

config = Config()
