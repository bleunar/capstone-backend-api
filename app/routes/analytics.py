from flask import Blueprint, jsonify, request
from .. services import database
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from ..config import config
from ..services.validation import check_json_payload, check_required_fields, check_order_parameter, common_success_response, common_error_response, common_database_error_response

bp_analytics = Blueprint("analytics", __name__)

@bp_analytics.route("/dashboard", methods=["GET"])
def get_dashboard():



    # execute query
    accounts_fetch = database.fetch

    # query fails
    if not accounts_fetch['success']:
        return common_database_error_response(accounts_fetch)

    # success
    return common_success_response(accounts_fetch['data'])



# Helpers

def account_data_counts():
    query = """
        SELECT
        COUNT(*) AS total,
        COUNT(CASE WHEN status = 'active' THEN 1 END) AS active,
        COUNT(CASE WHEN status = 'suspended' THEN 1 END) AS suspended
        FROM accounts;
    """

    