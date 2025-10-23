from flask import Blueprint, jsonify, request
from ..services.jwt import require_access
from ..services import database
from flask_jwt_extended import jwt_required
from ..services.validation import check_order_parameter, common_success_response, common_database_error_response
from ..config import config

bp_account_logs = Blueprint("account_logs", __name__)

@bp_account_logs.route("/", methods=["GET"])
@jwt_required()
@require_access("guest")
def get():
    # setup base query
    base_query = """
        SELECT
            al.id,
            al.account_id,
            al.action,
            al.created_at,
            a.username AS account_username,
            CONCAT_WS(' ', a.first_name, a.middle_name, a.last_name) AS account_full_name
        FROM account_logs AS al
        INNER JOIN accounts AS a
            ON al.account_id = a.id;
    """

    # CONDITIONALS
    conditional_query = []
    conditional_params = []


    # filter by id
    if 'id' in request.args and request.args.get('id').isdigit():
        conditional_query.append("al.id = %s")
        conditional_params.append()

    
    # filter by account id
    if 'account_id' in request.args and request.args.get('account_id'):
        conditional_query.append("al.account_id = %s")
        conditional_params.append(request.args.get('account_id'))


    # filter by action
    if 'action' in request.args and request.args.get('action'):
        conditional_query.append("al.action = %s")
        conditional_params.append(request.args.get('action'))


    # build conditional query
    if conditional_query:
        base_query += " WHERE " + " AND ".join(conditional_query)
        

    # ORDERING OF RECORDS BY RECENTLY CREATED
    if 'order' in request.args:
        order = check_order_parameter(request.args.get('order'))
        base_query += f" ORDER BY al.created_at {order}"
    
    # closing statements
    base_query += ";"

    # execute query
    account_logs_fetch = database.fetch_all(base_query, tuple(conditional_params))

    # query fails
    if not account_logs_fetch['success']:
        return common_database_error_response(account_logs_fetch)

    # success
    return common_success_response(account_logs_fetch['data'])

