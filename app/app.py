from flask import jsonify
import datetime
from zoneinfo import ZoneInfo
from app.config import config
from flask_cors import CORS
from app.services.system import get_service_information
from app.services.core import get_flask_app
from app.services.system import system_check

app = get_flask_app()
app.config["SECRET_KEY"] = config.FLASK_SECRET_KEY
app.config["JWT_SECRET_KEY"] = config.JWT_SECRET_KEY
app.config["JWT_TOKEN_LOCATION"] = ["headers","cookies"]
app.config["JWT_COOKIE_SECURE"] = True
app.config["JWT_COOKIE_SAMESITE"] = "None"
app.config["JWT_COOKIE_HTTPONLY"] = True
app.config["JWT_COOKIE_CSRF_PROTECT"] = True
app.url_map.strict_slashes = False

# ENDPOINTS FROM BLUEPRINTS
from app.routes.access_levels import access_levels_bp
app.register_blueprint(access_levels_bp, url_prefix="/access_levels")

from app.routes.account_settings import bp_account_settings
app.register_blueprint(bp_account_settings, url_prefix="/account_settings")

from app.routes.account_roles import bp_account_roles
app.register_blueprint(bp_account_roles, url_prefix="/account_roles")

from app.routes.account_logs import bp_account_logs
app.register_blueprint(bp_account_logs, url_prefix="/account_logs")

from app.routes.accounts import bp_accounts
app.register_blueprint(bp_accounts, url_prefix="/accounts")

from app.routes.locations import bp_locations
app.register_blueprint(bp_locations, url_prefix="/locations")

from app.routes.equipment_sets import bp_equipment_sets
app.register_blueprint(bp_equipment_sets, url_prefix="/equipment_sets")

from app.routes.equipment_set_components import bp_equipment_set_components
app.register_blueprint(bp_equipment_set_components, url_prefix="/equipment_set_components")

from app.routes.equipment_set_history import bp_equipment_set_history
app.register_blueprint(bp_equipment_set_history, url_prefix="/equipment_set_history")

ph_time = datetime.datetime.now(ZoneInfo("Asia/Manila"))

# status endpoint
@app.route("/", methods=["GET"])
def status():
    data = {
        "msg": "api services is up",
        "date": str(ph_time),
        "info": get_service_information()
    }
    return jsonify(data)

# setup CORS for all endpoint
CORS(app, origins=config.WEB_CLIENT_HOSTS, supports_credentials=True)

# main method
def jarvis_deploy_website():
    system_check()
    
    return app