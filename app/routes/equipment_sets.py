from flask import Blueprint, jsonify, request
from app.services.jwt import require_access
from app.services.security import generate_id
import app.services.database as database
from flask_jwt_extended import jwt_required
from app.config import config

bp_equipment_sets = Blueprint("equipment_sets", __name__)

@bp_equipment_sets.route("/", methods=["GET"])
@jwt_required()
@require_access("guest")
def get():

    # setup base query
    base_query = """
        select
            eq_set.id,
            eq_set.location_id,
            eq_set.location_set_number,

            eq_set.requires_avr,
            eq_set.requires_headset,
            eq_set.requires_camera,

            eq_set.plugged_power_cable,
            eq_set.plugged_display_cable,

            eq_set.internet_connectivity,
            eq_set.functionability,
            
            eq_set.status,
            eq_set.issue_description,

            eq_set.created_at,
            eq_set.updated_at
        from equipment_sets as eq_set
    """

    # CONDITIONALS
    conditional_query = []
    conditional_params = []


    # filter by id
    if 'id' in request.args:
        conditional_query.append("eq_set.id = %s")
        conditional_params.append(request.args.get('id'))

    
    # filter by location_id
    if 'location_id' in request.args:
        conditional_query.append("eq_set.location_id = %s")
        conditional_params.append(request.args.get('id'))


    # build conditional query
    if conditional_query:
        base_query += " WHERE " + " AND ".join(conditional_query)
    
    # sort the order by ascending
    base_query += f" ORDER BY eq_set.location_set_number ASC"
    

    # closing statements
    base_query += ";"

    # execute query
    equipment_set_fetch = database.fetch_all(base_query, tuple(conditional_params))

    # query fails
    if not equipment_set_fetch['success']:
        result = jsonify({
            "msg": equipment_set_fetch['msg']
        })
        return result, 400

    # success
    return jsonify({
        "data": equipment_set_fetch['data']
    }), 200


@bp_equipment_sets.route("/", methods=["POST"])
@require_access('admin')
def add():
    data = request.get_json()

    # setup and fetch data
    location_id = data.get('location_id')
    location_set_number = data.get('location_set_number')

    requires_avr = data.get('requires_avr', 'true')
    requires_headset = data.get('requires_headset', 'true')
    requires_camera = data.get('requires_camera', 'true')

    plugged_power_cable = data.get('plugged_power_cable', 'true')
    plugged_display_cable = data.get('plugged_display_cable', 'true')

    internet_connectivity = data.get('internet_connectivity', 'stable')
    functionability = data.get('functionability', 'stable')

    status = data.get('status', 'active')


    if any(item is None for item in [location_id, requires_avr, requires_camera, requires_headset, plugged_display_cable, plugged_power_cable, internet_connectivity, functionability, status]):
        return jsonify({
            "msg": "forms data incomplete"
        }), 400
    

    base_query = """
        insert into equipment_sets
            (
                equipment_sets.id,
                equipment_sets.location_id,
                equipment_sets.location_set_number,
                equipment_sets.requires_avr,
                equipment_sets.requires_headset,
                equipment_sets.requires_camera,
                equipment_sets.plugged_power_cable,
                equipment_sets.plugged_display_cable,
                equipment_sets.internet_connectivity,
                equipment_sets.functionability,
                equipment_sets.status
            )
        values
            (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
    """
    base_params = (
        generate_id(),
        location_id,
        location_set_number,
        requires_avr,
        requires_headset,
        requires_camera,
        plugged_power_cable,
        plugged_display_cable,
        internet_connectivity,
        functionability,
        status
    )

    equipment_set_added = database.execute_single(base_query, base_params)

    if not equipment_set_added['success']:
        result = jsonify({
            "msg": equipment_set_added['msg']
        })
        return result, 400

    result = jsonify({
        "data": True
    })
    return result, 200



@bp_equipment_sets.route("/<id>", methods=["PUT"])
@require_access('admin')
def edit(id):
    data = request.get_json()

    # fetch data forms
    location_id = data.get('location_id')
    location_set_number = data.get('location_set_number')

    requires_avr = data.get('requires_avr', 'false')
    requires_headset = data.get('requires_headset', 'false')
    requires_camera = data.get('requires_camera', 'false')

    plugged_power_cable = data.get('plugged_power_cable', 'true')
    plugged_display_cable = data.get('plugged_display_cable', 'true')

    internet_connectivity = data.get('internet_connectivity', 'stable')
    functionability = data.get('functionability', 'stable')

    status = data.get('status', 'active')
    issue_description = data.get('issue_description', '')
    

    if any(item is None for item in [location_id, location_set_number, requires_avr, requires_camera, requires_headset, plugged_display_cable, plugged_power_cable, internet_connectivity, functionability, status]):
        return jsonify({
            "msg": "forms data incomplete"
        }), 400

    # prepare query and parameters
    base_query = """
        update equipment_sets set
            equipment_sets.id = %s,
            equipment_sets.location_id = %s,
            equipment_sets.location_set_number = %s,
            equipment_sets.requires_avr = %s,
            equipment_sets.requires_headset = %s,
            equipment_sets.requires_camera = %s,
            equipment_sets.plugged_power_cable = %s,
            equipment_sets.plugged_display_cable = %s,
            equipment_sets.internet_connectivity = %s,
            equipment_sets.functionability = %s,
            equipment_sets.status = %s,
            equipment_sets.issue_description = %s
        
        where
            equipment_sets.id = %s
    """

    base_params = (
        location_id,
        location_set_number,
        requires_avr,
        requires_headset,
        requires_camera,
        plugged_power_cable,
        plugged_display_cable,
        internet_connectivity,
        functionability,
        status,
        issue_description,
        id    
    )

    equipment_set_updated = database.execute_single(base_query, base_params)

    if not equipment_set_updated['success']:
        result = jsonify({
            "msg": equipment_set_updated['msg']
        })
        return result, 400

    result = jsonify({
        "data": True
    })
    return result, 200


# hard delete
@bp_equipment_sets.route("/<id>", methods=["DELETE"])
@require_access('admin')
def delete(id):

    # prepare query and parameters
    base_query = """
        delete from equipment_sets
        where
            equipment_sets.id = %s;
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

