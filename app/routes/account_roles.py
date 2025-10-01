from flask import Blueprint, jsonify, request
from app.services.jwt import require_access
from app.services.security import generate_id
import app.services.database as database
from flask_jwt_extended import jwt_required
from app.config import config
from app.services.validation import check_json_payload, check_required_fields, check_order_parameter, common_success_response, common_error_response, common_database_error_response

bp_account_roles = Blueprint("account_roles", __name__)

@bp_account_roles.route("/", methods=["GET"])
@jwt_required()
@require_access("guest")
def get():

    # setup base query
    base_query = """
        select
            ar.id,
            ar.name,
            ar.access_level,
            ar.created_at,
            ar.updated_at
        from account_roles as ar
    """

    # CONDITIONALS
    conditional_query = []
    conditional_params = []


    # filter by id
    if 'id' in request.args and request.args.get('id'):
        conditional_query.append("ar.id = %s")
        conditional_params.append(request.args.get('id'))


    # filter by search
    if 'name' in request.args and request.args.get('name'):
        conditional_query.append("ar.name = %s")
        conditional_params.append(request.args.get('name'))

    # build conditional query
    if conditional_query:
        base_query += " WHERE " + " AND ".join(conditional_query)
        

    # ORDERING OF RECORDS BY RECENTLY CREATED
    if 'order' in request.args:
        order = check_order_parameter(request.args.get('order'))
        base_query += f" ORDER BY ar.created_at {order}"
    
    # closing statements
    base_query += ";"

    # execute query
    account_roles_fetch = database.fetch_all(base_query, tuple(conditional_params))

    # query fails
    if not account_roles_fetch['success']:
        return common_database_error_response(account_roles_fetch)

    # success
    return common_success_response(account_roles_fetch['data'])


@bp_account_roles.route("/", methods=["POST"])
@require_access('root', exact=True)
def add():
    # Validate JSON payload
    data, error_response = check_json_payload()
    if error_response:
        return error_response

    # Validate required fields
    required_fields = ['name']
    validation_error = check_required_fields(data, required_fields)
    if validation_error:
        return validation_error

    # setup and fetch data
    name = data.get('name')
    access_level = data.get('access_level', '5')

    if any(item is None for item in [name, access_level]):
        return jsonify({
            "msg": "forms data incomplete"
        }), 400

    # prevent duplicate root roles
    root_role_exists = database.fetch_scalar("select account_roles.id from account_roles where account_roles.access_level = 0;")

    if root_role_exists['success'] and root_role_exists['data'] and str(access_level) == '0':
        return jsonify({
            "msg": "only single root role should exist"
        }), 400

    # prevent duplicate name

    base_query = """
        insert into account_roles
            (
                account_roles.name,
                account_roles.access_level
            )
        values
            (%s, %s);
    """

    base_params = (name, access_level)

    account_roles_added = database.execute_single(base_query, base_params)

    if not account_roles_added['success']:
        result = jsonify({
            "msg": account_roles_added['msg']
        })
        return result, 400

    result = jsonify({
        "data": True
    })
    return result, 200



@bp_account_roles.route("/<id>", methods=["PUT"])
@require_access('root')
def edit(id):
    data = request.get_json()

    # fetch data forms
    name = data.get('name')
    access_level = data.get('access_level', 5)

    # fetch the existing root role
    root_role_query = database.fetch_one("select id from account_roles where access_level = 0;")

    # check if the user is editing a role as root
    if str(access_level) == '0':
        # Check if a root role exists
        if root_role_query['success'] and root_role_query['data']:
            existing_root_id = root_role_query['data']['id']

            # Check if existing root role is different from the target role to edit
            if str(existing_root_id) != str(id):
                return jsonify({
                    "msg": "A 'root' role with access_level 0 already exists."
                }), 400
    
    if not name and not access_level:
        return jsonify({
            "msg": "data incomplete"
        }), 400

    # prepare query and parameters
    base_query = """
        update account_roles set
            account_roles.name = %s,
            account_roles.access_level = %s
        
        where
            account_roles.id = %s
    """

    base_params = (name, access_level, id)

    account_roles_updated = database.execute_single(base_query, base_params)

    if not account_roles_updated['success']:
        result = jsonify({
            "msg": account_roles_updated['msg']
        })
        return result, 400

    result = jsonify({
        "data": True
    })
    return result, 200


# hard delete
@bp_account_roles.route("/<id>", methods=["DELETE"])
@require_access('root')
def delete(id):

    # prepare query and parameters
    base_query = """
        delete from account_roles
        where
            account_roles.id = %s;
    """
    base_params = (id, )

    # execute query
    account_roles_deleted = database.execute_single(base_query, base_params)

    # if fail
    if not account_roles_deleted['success']:
        result = jsonify({
            "msg": account_roles_deleted['msg']
        })
        return result, 400

    # confirm deletion
    result = jsonify({
        "data": True
    })
    return result, 200