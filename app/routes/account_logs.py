from flask import Blueprint, jsonify, request
from app.services.jwt import require_access
import app.services.database as database
from flask_jwt_extended import jwt_required
from app.config import config

bp_account_logs = Blueprint("account_logs", __name__)

@bp_account_logs.route("/", methods=["GET"])
@jwt_required()
@require_access("guest")
def get():
    # setup base query
    base_query = """
        select
            al.id,
            al.account_id,
            al.action,
            al.created_at,
            a.username as account_username,
            a.first_name as account_first_name,
            a.middle_name as account_middle_name,
            a.last_name as account_last_name
        from account_logs as al
        inner join accounts as a on al.account_id = a.id
    """

    # CONDITIONALS
    conditional_query = []
    conditional_params = []


    # filter by id
    if 'id' in request.args:
        conditional_query.append("al.id = %s")
        conditional_params.append(request.args.get('id'))

    
    # filter by account id
    if 'account_id' in request.args:
        conditional_query.append("al.account_id = %s")
        conditional_params.append(request.args.get('account_id'))


    # filter by action
    if 'action' in request.args:
        conditional_query.append("al.action = %s")
        conditional_params.append(request.args.get('action'))


    # build conditional query
    if conditional_query:
        base_query += " WHERE " + " AND ".join(conditional_query)
        

    # ORDERING OF RECORDS BY RECENTLY CREATED
    if 'order' in request.args:
        order = "DESC" if request.args.get('order') == "latest" else "ASC"
        base_query += f" ORDER BY al.created_at {order}"
    
    # closing statements
    base_query += ";"

    # execute query
    account_logs_fetch = database.fetch_all(base_query, tuple(conditional_params))

    # query fails
    if not account_logs_fetch['success']:
        result = jsonify({
            "msg": account_logs_fetch['msg']
        })
        return result, 400

    # success
    return jsonify({
        "data": account_logs_fetch['data']
    }), 200

