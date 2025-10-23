from flask import Blueprint, jsonify, request
from ..services.jwt import require_access
from ..services.security import generate_id
from ..services import database
from flask_jwt_extended import jwt_required
from ..config import config
from ..services.validation import check_json_payload, check_required_fields, check_order_parameter, common_success_response, common_database_error_response
from ..services.security import generate_username, generate_default_password, generate_uuid

bp_system = Blueprint("system", __name__)

@bp_system.route("/format_username", methods=["GET"])
def format_username():
    data, error_response = check_json_payload()
    if error_response:
        return error_response
    
    first_name = data.get("first_name")
    middle_name = data.get("middle_name")
    last_name = data.get("last_name")

    common_success_response(
        data=generate_username(first_name, middle_name, last_name)
    )

@bp_system.route("/generate_password", methods=["GET"])
def generate_password():
    data, error_response = check_json_payload()
    if error_response:
        return error_response
    
    first_name = data.get("first_name")
    middle_name = data.get("middle_name")
    last_name = data.get("last_name")

    common_success_response(
        data=generate_default_password(first_name, middle_name, last_name)
    )

@bp_system.route("/generate_uuid", methods=["GET"])
def generate_uuid_endpoint():

    return common_success_response(
        data=generate_uuid()
    )