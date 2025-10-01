import mysql.connector
from app.config import config
import json
import smtplib
from flask_jwt_extended import JWTManager
from flask import Flask
from app.services.log import log

# instance of flask and jwt
app = Flask(__name__)
jwt = JWTManager(app)


# instance fetch
def get_flask_app():
    return app

def get_jwt_manager():
    return jwt


try:
    connection_pool = mysql.connector.pooling.MySQLConnectionPool(
        pool_name="conn-pool-auth",
        pool_size=int(config.MYSQL_POOL_SIZE),
        host=config.MYSQL_HOST,
        port=int(config.MYSQL_PORT),
        user=config.MYSQL_USER,
        password=config.MYSQL_PASSWORD,
        database=config.MYSQL_DB,
        use_pure=True
    )
    log.inform("DATABASE", "Connection pool created successfully")

except mysql.connector.Error as err:
    log.error("DATABASE", f"Error creating connection pool: {err}")
    connection_pool = None


def get_db_connection():
    if connection_pool is None:
        log.error("DATABASE", "Connection pool is not available.")
        return None
        
    try:
        conn = connection_pool.get_connection()
        return conn
        
    except mysql.connector.Error as err:
        log.error("DATABASE", f"Error getting connection from pool: {err}")
        return None


# fetching mail server
def get_mail_server():
    try:
        server = smtplib.SMTP(config.MAIL_SERVER_ADDRESS, int(config.MAIL_SERVER_PORT))
        server.starttls()
        server.login(config.MAIL_ADDRESS, config.MAIL_PASSKEY)
        return server
    except smtplib.SMTPException as e:
        log.error("MAIL_SRV-ERR", f"SMTP error: {str(e)}")
        return None
    except Exception as e:
        log.error("MAIL_SRV-ERR", f"Failed to connect with mail server: {str(e)}")
        return None