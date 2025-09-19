from flask import Blueprint, jsonify, request
from services.jwt import require_access
from services.security import generate_id
import services.database as database
from flask_jwt_extended import jwt_required
from config import config

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
    if 'id' in request.args:
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
        order = "DESC" if request.args.get('order') == "latest" else "ASC"
        base_query += f" ORDER BY loc.created_at {order}"
    
    # closing statements
    base_query += ";"

    # execute query
    locations_fetch = database.fetch_all(base_query, tuple(conditional_params))

    # query fails
    if not locations_fetch['success']:
        result = jsonify({
            "msg": locations_fetch['msg']
        })
        return result, 400

    # success
    return jsonify({
        "data": locations_fetch['data']
    }), 200


@bp_locations.route("/", methods=["POST"])
@require_access('admin')
def add():
    data = request.get_json()

    # setup and fetch data
    name = data.get('name')
    description = data.get('description', '')
    equipment_layout = data.get('equipment_layout', '')


    if any(item is None for item in [name, description, equipment_layout ]):
        return jsonify({
            "msg": "forms data incomplete"
        }), 400

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