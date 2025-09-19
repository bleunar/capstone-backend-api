import os
from dotenv import load_dotenv
import app.services.access
load_dotenv()

# default key if missing
default_key = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

class Config:
    BACKEND_ADDRESS = os.environ.get("BACKEND_ADDRESS")
    BACKEND_PORT = os.environ.get("BACKEND_PORT")
    FLASK_ENVIRONMENT = os.environ.get("FLASK_ENVIRONMENT")

    # flask server
    FLASK_SECRET_KEY = os.environ.get("SECRET_NI_FLASK")

    JWT_SECRET_KEY = os.environ.get("SECRET_NI_JWT")

    # mail server credentials
    MAIL_ADDRESS = os.environ.get("MAIL_ADDRESS")
    MAIL_PASSKEY =  os.environ.get("MAIL_PASSKEY")

    # default admin email
    ROOT_ADMIN_USERNAME = os.environ.get("ROOT_ADMIN_USERNAME")
    ROOT_ADMIN_FIRST_NAME = os.environ.get("ROOT_ADMIN_FIRST_NAME")
    ROOT_ADMIN_MIDDLE_NAME = os.environ.get("ROOT_ADMIN_MIDDLE_NAME")
    ROOT_ADMIN_LAST_NAME = os.environ.get("ROOT_ADMIN_LAST_NAME")
    ROOT_ADMIN_EMAIL = os.environ.get("ROOT_ADMIN_EMAIL")
    ROOT_ADMIN_PASSWORD = os.environ.get("ROOT_ADMIN_PASSWORD")

    # database
    MYSQL_HOST = os.environ.get("MYSQL_HOST")
    MYSQL_PORT = os.environ.get("MYSQL_PORT")
    MYSQL_DB = os.environ.get("MYSQL_DATABASE")
    MYSQL_USER = os.environ.get("MYSQL_USER")
    MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD")

    # web client
    WEB_CLIENT_HOSTS = [url.strip() for url in os.environ.get("WEB_CLIENT_HOSTS").split(',')]

    access_levels = app.services.access.access_level_lookup()

config = Config()