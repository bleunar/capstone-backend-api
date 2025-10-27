from flask import Blueprint, jsonify, request
from ..services.jwt import require_access
from .. services import database
from ..services.security import generate_id, generate_username, generate_default_password
from werkzeug.security import generate_password_hash
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from ..config import config
from ..services.validation import check_json_payload, check_required_fields, check_order_parameter, common_success_response, common_error_response, common_database_error_response

bp_accounts = Blueprint("accounts", __name__)

@bp_accounts.route("/", methods=["GET"])
@bp_accounts.route("/<id>", methods=["GET"])
@jwt_required()
@require_access("guest")
def get(id=None):

    current_user_claims = get_jwt()

    # setup base query
    base_query = """
        SELECT
            a.id,
            a.role_id,
            ar.name AS role_name,
            ar.access_level,
            CONCAT(
                a.first_name,
                IF(a.middle_name IS NOT NULL AND a.middle_name != '', CONCAT(' ', a.middle_name), ''),
                ' ',
                a.last_name
            ) AS full_name,
            a.gender,
            DATE_FORMAT(a.birth_date, '%Y-%m-%d') AS birth_date,
            a.email,
            a.username,
            a.created_at,
            a.updated_at
        FROM accounts AS a
        INNER JOIN account_roles AS ar ON a.role_id = ar.id;
    """

    # CONDITIONALS
    conditional_query = []
    conditional_params = []


    # filter by id
    if 'id' in request.args and request.args.get("id"):
        conditional_query.append("a.id = %s")
        conditional_params.append(request.args.get('id'))


    # filter by search
    if 'username' in request.args and request.args.get("username"):
        conditional_query.append("a.username = %s")
        conditional_params.append(request.args.get('username'))

    if 'email' in request.args and request.args.get("email"):
        conditional_query.append("a.email = %s")
        conditional_params.append(request.args.get('email'))
    
    # only show items with "active" status on non administrator
    if current_user_claims['acc'] > 1:
        conditional_query.append("a.status = 'active'")

    # build conditional query
    if conditional_query:
        base_query += " WHERE " + " AND ".join(conditional_query)
        

    # ORDERING OF RECORDS BY RECENTLY CREATED
    if 'order' in request.args:
        order = check_order_parameter(request.args.get('order'))
        base_query += f" ORDER BY a.created_at {order}"
    
    # closing statements
    base_query += ";"

    # execute query
    accounts_fetch = database.fetch_all(base_query, tuple(conditional_params))

    # query fails
    if not accounts_fetch['success']:
        return common_database_error_response(accounts_fetch)

    # success
    return common_success_response(accounts_fetch['data'])


@bp_accounts.route("/", methods=["POST"])
@require_access('admin')
def add():
    # Validate JSON payload
    data, error_response = check_json_payload()
    if error_response:
        return error_response

    # Validate required fields
    required_fields = ['role_id', 'first_name', 'last_name', 'email']
    validation_error = check_required_fields(data, required_fields)
    if validation_error:
        return validation_error

    # setup and fetch data
    role_id = data['role_id']
    first_name = data['first_name']
    middle_name = data.get('middle_name', '')
    last_name = data['last_name']
    gender = data['gender']
    birth_date = data['birth_date']
    email = data['email']
    username = data.get('username', '')
    password = data.get('password', '')
    status = data.get('status', 'active')


    # assign password from data if password is set, else, generate a new password using user's names, organization, and a unique string
    account_password = password if password else generate_default_password(first_name, middle_name, last_name)
    account_password_hashed = generate_password_hash(account_password)

    base_query = """
        insert into accounts
            (
                accounts.id,
                accounts.role_id,
                accounts.first_name,
                accounts.middle_name,
                accounts.last_name,
                accounts.gender,
                accounts.birth_date,
                accounts.email,
                accounts.username,
                accounts.password_hash,
                accounts.status
            )
        values
            (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
    """
    base_params = (
        generate_id(),
        role_id,
        first_name,
        middle_name if middle_name else None,
        last_name,
        gender,
        birth_date,
        email,
        username,
        account_password_hashed,
        status
    )

    accounts_added = database.execute_single(base_query, base_params)

    if not accounts_added['success']:
        return common_database_error_response(accounts_added)

    return common_success_response(
        message="Account created successfully",
        data={
            "username": username,
            "password": account_password
        }
    )



@bp_accounts.route("/", methods=["PUT"])
@bp_accounts.route("/<id>", methods=["PUT"])
@require_access('root')
def edit(id=None):
    # Validate JSON payload
    data, error_response = check_json_payload()
    if error_response:
        return error_response

    if id is None:
        id = get_jwt_identity()

    account_database_check = database.fetch_scalar('select accounts.password_hash from accounts where accounts.id = %s;', (id, ))

    if account_database_check['success'] is False:
        return common_database_error_response(account_database_check)

    # Validate required fields
    required_fields = ['role_id', 'first_name', 'last_name', 'email']
    validation_error = check_required_fields(data, required_fields)
    if validation_error:
        return validation_error

    # fetch data forms
    role_id = data['role_id']
    first_name = data['first_name']
    middle_name = data.get('middle_name', '')
    last_name = data['last_name']
    gender = data['gender']
    birth_date = data['birth_date']
    email = data['email']
    username = data.get('username', '')
    status = data.get('status', 'active')

    print(data['birth_date'])


    # prepae query and paameters
    base_query = """
        update accounts set
            accounts.role_id = %s,
            accounts.first_name = %s,
            accounts.middle_name = %s,
            accounts.last_name = %s,
            accounts.gender = %s,
            accounts.birth_date = %s,
            accounts.email = %s,
            accounts.username = %s,
            accounts.status = %s
        where
            accounts.id = %s;
    """

    base_params = (
        role_id,
        first_name,
        middle_name if middle_name else None,
        last_name,
        gender,
        birth_date,
        email,
        username,
        status,
        id
    )

    accounts_updated = database.execute_single(base_query, base_params)

    if not accounts_updated['success']:
        return common_database_error_response(accounts_updated)

    return common_success_response(
        message="Account Updated"
    )


# handle delete
@bp_accounts.route("/<id>", methods=["DELETE"])
@require_access('root')
def delete(id):

    current_user_id = get_jwt_identity()

    if id == current_user_id:
        return jsonify({
            "msg": "You cannot delete your own account"
        }), 400

    # prepare query and paameters
    base_query = """
        delete from accounts
        where
            accounts.id = %s;
    """
    base_params = (id, )

    # execute query
    accounts_deleted = database.execute_single(base_query, base_params)

    # if deletion failed
    if not accounts_deleted['success']:
        result = jsonify({
            "msg": accounts_deleted['msg']
        })
        return result, 400

    # confirm deletion
    result = jsonify({
        "data": True
    })
    return result, 200


# ANALYTICSSSSS ==================================================================

@bp_accounts.route("/analytics/total", methods=["GET"])
def analytics_total():
    query = """
        SELECT COUNT(id) AS data
        FROM accounts;
    """

    # execute query
    accounts_analytics_fetch_total = database.fetch_scalar(query)

    # query fails
    if not accounts_analytics_fetch_total['success']:
        return common_database_error_response(accounts_analytics_fetch_total)
    
    # success
    return common_success_response(accounts_analytics_fetch_total['data'])

@bp_accounts.route("/analytics/total_active", methods=["GET"])
def analytics_total_active():
    query = """
        SELECT COUNT(DISTINCT account_id) AS total
        FROM account_logs
        WHERE action = 'login'
          AND created_at >= NOW() - INTERVAL 1 HOUR;
    """

    # execute query
    accounts_analytics_fetch_total_active = database.fetch_scalar(query)

    # query fails
    if not accounts_analytics_fetch_total_active['success']:
        return common_database_error_response(accounts_analytics_fetch_total_active)
    
    # success
    return common_success_response(accounts_analytics_fetch_total_active['data'])


@bp_accounts.route("/analytics/total_activity", methods=["GET"])
def analytics_total_activity():
    query = """
        SELECT COUNT(DISTINCT account_id) AS total
        FROM account_logs
        WHERE created_at >= NOW() - INTERVAL 24 HOUR;
    """

    # execute query
    accounts_analytics_fetch_total_activity = database.fetch_scalar(query)

    # query fails
    if not accounts_analytics_fetch_total_activity['success']:
        return common_database_error_response(accounts_analytics_fetch_total_activity)
    
    # success
    return common_success_response(accounts_analytics_fetch_total_activity['data'])