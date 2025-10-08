from flask import jsonify
import datetime
from zoneinfo import ZoneInfo
from .config import config
from flask_cors import CORS
from .services.system import get_service_information
from .services.core import get_flask_app
from .services.system import system_check

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
from .routes.access_levels import access_levels_bp
app.register_blueprint(access_levels_bp, url_prefix="/access_levels")

from .routes.account_settings import bp_account_settings
app.register_blueprint(bp_account_settings, url_prefix="/account_settings")

from .routes.account_roles import bp_account_roles
app.register_blueprint(bp_account_roles, url_prefix="/account_roles")

from .routes.account_logs import bp_account_logs
app.register_blueprint(bp_account_logs, url_prefix="/account_logs")

from .routes.accounts import bp_accounts
app.register_blueprint(bp_accounts, url_prefix="/accounts")

from .routes.locations import bp_locations
app.register_blueprint(bp_locations, url_prefix="/locations")

from .routes.equipment_sets import bp_equipment_sets
app.register_blueprint(bp_equipment_sets, url_prefix="/equipment_sets")

from .routes.equipment_set_components import bp_equipment_set_components
app.register_blueprint(bp_equipment_set_components, url_prefix="/equipment_set_components")

from .routes.equipment_set_history import bp_equipment_set_history
app.register_blueprint(bp_equipment_set_history, url_prefix="/equipment_set_history")

# ANALYTICS ENDPOINTS
from .routes.analytics.accounts import bp_analytics_accounts
app.register_blueprint(bp_analytics_accounts, url_prefix="/analytics/accounts")

from .routes.analytics.equipment import bp_analytics_equipment
app.register_blueprint(bp_analytics_equipment, url_prefix="/analytics/equipment")

from .routes.analytics.activity import bp_analytics_activity
app.register_blueprint(bp_analytics_activity, url_prefix="/analytics/activity")

from .routes.analytics.overview import bp_analytics_overview
app.register_blueprint(bp_analytics_overview, url_prefix="/analytics/overview")

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