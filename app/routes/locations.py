from flask import Blueprint, jsonify, request
from app.services.jwt import require_access
from app.services.security import generate_id
import app.services.database as database
from flask_jwt_extended import jwt_required
from app.config import config
from app.services.validation import check_json_payload, check_required_fields, check_order_parameter, common_success_response, common_database_error_response

bp_locations = Blueprint("locations", __name__)

@bp_locations.route("/", methods=["GET"])
@jwt_required()
@require_access("guest")
def get():

    # setup base query
    base_query = """
        select
            loc.id,
            loc.name,
            loc.description,
            loc.equipment_layout,
            loc.created_at,
            loc.updated_at
        from locations as loc
    """

    # CONDITIONALS
    conditional_query = []
    conditional_params = []


    # filter by id
    if 'id' in request.args and request.args.get('id'):
        conditional_query.append("loc.id = %s")
        conditional_params.append(request.args.get('id'))


    # filter by search
    if 'name' in request.args:
        conditional_query.append("loc.name = %s")
        conditional_params.append(request.args.get('name'))

    # build conditional query
    if conditional_query:
        base_query += " WHERE " + " AND ".join(conditional_query)
        

    # ORDERING OF RECORDS BY RECENTLY CREATED
    if 'order' in request.args:
        order = check_order_parameter(request.args.get('order'))
        base_query += f" ORDER BY loc.created_at {order}"
    
    # closing statements
    base_query += ";"

    # execute query
    locations_fetch = database.fetch_all(base_query, tuple(conditional_params))

    # query fails
    if not locations_fetch['success']:
        return common_database_error_response(locations_fetch)

    # success
    return common_success_response(locations_fetch['data'])


@bp_locations.route("/", methods=["POST"])
@require_access('admin')
def add():
    # Validate JSON payload
    data, error_response = check_json_payload()
    if error_response:
        return error_response

    # Validate required fields
    required_fields = ['name', 'description', 'equipment_layout']
    validation_error = check_required_fields(data, required_fields)
    if validation_error:
        return validation_error

    # setup and fetch data
    name = data['name']
    description = data['description']
    equipment_layout = data['equipment_layout']

    base_query = """
        insert into locations
            (
                locations.id,
                locations.name,
                locations.description,
                locations.equipment_layout
            )
        values
            (%s, %s, %s, %s);
    """
    base_params = (
        generate_id(),
        name,
        description,
        equipment_layout
    )

    location_added = database.execute_single(base_query, base_params)

    if not location_added['success']:
        result = jsonify({
            "msg": location_added['msg']
        })
        return result, 400

    result = jsonify({
        "data": True
    })
    return result, 200



@bp_locations.route("/<id>", methods=["PUT"])
@require_access('admin')
def edit(id):
    data = request.get_json()

    # fetch data forms
    name = data['name']
    description = data['description']
    equipment_layout = data['equipment_layout']
    
    if any(item is None for item in [name, description, equipment_layout]):
        return jsonify({
            "msg": "data incomplete"
        }), 400

    # prepare query and parameters
    base_query = """
        update locations set
            locations.name = %s,
            locations.description = %s,
            locations.equipment_layout = %s
        
        where
            locations.id = %s
    """

    base_params = (name, description, equipment_layout, id)

    location_updated = database.execute_single(base_query, base_params)

    if not location_updated['success']:
        result = jsonify({
            "msg": location_updated['msg']
        })
        return result, 400

    result = jsonify({
        "data": True
    })
    return result, 200


# hard delete
@bp_locations.route("/<id>", methods=["DELETE"])
@require_access('admin')
def delete(id):

    # prepare query and parameters
    base_query = """
        delete from locations
        where
            locations.id = %s;
    """
    base_params = (id, )

    # execute query
    location_deleted = database.execute_single(base_query, base_params)

    # if fail
    if not location_deleted['success']:
        result = jsonify({
            "msg": location_deleted['msg']
        })
        return result, 400

    # confirm deletion
    result = jsonify({
        "data": True
    })
    return result, 200