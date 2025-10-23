from flask import Blueprint, jsonify, request
from ..services.jwt import require_access
from ..services.security import generate_id
from ..services import database
from flask_jwt_extended import jwt_required
from ..config import config
from .equipment_set_components import initialize_equipment_set_components
from ..services.validation import check_json_payload, check_required_fields, common_success_response, common_error_response, common_database_error_response

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
            eq_set.name,

            eq_set.requires_avr,
            eq_set.requires_headset,

            eq_set.plugged_power_cable,
            eq_set.plugged_display_cable,

            eq_set.connectivity,
            eq_set.performance,
            
            eq_set.status,
            eq_set.issue,

            eq_set.created_at,
            eq_set.updated_at
        from equipment_sets as eq_set
    """

    # CONDITIONALS
    conditional_query = []
    conditional_params = []


    # filter by id
    if 'id' in request.args and request.args.get('id'):
        conditional_query.append("eq_set.id = %s")
        conditional_params.append(request.args.get('id'))

    
    # filter by location_id
    if 'location_id' in request.args and request.args.get('location_id'):
        conditional_query.append("eq_set.location_id = %s")
        conditional_params.append(request.args.get('location_id'))


    # build conditional query
    if conditional_query:
        base_query += " WHERE " + " AND ".join(conditional_query)
    
    # sort the order by ascending
    base_query += f"ORDER BY CAST(REGEXP_REPLACE(name, '[^0-9]', '') AS UNSIGNED);"
    

    # closing statements
    base_query += ";"

    # execute query
    equipment_set_fetch = database.fetch_all(base_query, tuple(conditional_params))

    # query fails
    if not equipment_set_fetch['success']:
        return common_database_error_response(equipment_set_fetch)

    # success
    return common_success_response(equipment_set_fetch['data'])


@bp_equipment_sets.route("/single", methods=["POST"])
@require_access('admin')
def add_single():
    # Validate JSON payload
    data, error_response = check_json_payload()
    if error_response:
        return error_response

    # Validate required fields
    required_fields = ['location_id', 'name']
    validation_error = check_required_fields(data, required_fields)
    if validation_error:
        return validation_error

    # setup and fetch data
    location_id = data['location_id']
    name = data['name']

    requires_avr = "true" if data.get('requires_avr') else "false"
    requires_headset = "true" if data.get('requires_headset') else "false"
    id = generate_id()

    base_query = """
        insert into equipment_sets
            (
                equipment_sets.id,
                equipment_sets.location_id,
                equipment_sets.name,
                equipment_sets.requires_avr,
                equipment_sets.requires_headset
            )
        values
            (%s, %s, %s, %s, %s);
    """
    base_params = (
        id,
        location_id,
        name,
        requires_avr,
        requires_headset
    )

    equipment_set_added = database.execute_single(base_query, base_params)

    initialize_equipment_set_components(id, data)

    if not equipment_set_added['success']:
        return common_database_error_response(equipment_set_added)

    return common_success_response(
        data=True,
        message="Successfuly Added a New Equipment"
    )


@bp_equipment_sets.route("/batch", methods=["POST"])
@require_access('admin')
def add_batch():
    # Validate JSON payload
    data, error_response = check_json_payload()
    if error_response:
        return error_response

    # Validate required fields
    required_fields = ['location_id', 'prefix', 'count']
    validation_error = check_required_fields(data, required_fields)
    if validation_error:
        return validation_error

    # Setup and fetch data
    location_id = data['location_id']
    prefix = data['prefix']
    count = int(data['count'])

    requires_avr = "true" if data.get('requires_avr') else "false"
    requires_headset = "true" if data.get('requires_headset') else "false"

    # SQL query template
    base_query = """
        INSERT INTO equipment_sets
            (id, location_id, name, requires_avr, requires_headset)
        VALUES
            (%s, %s, %s, %s, %s);
    """

    added_sets = []
    failed_sets = []

    # Loop to add multiple equipment sets
    for i in range(1, count + 1):
        name = f"{prefix}{i}"
        set_id = generate_id()

        params = (
            set_id,
            location_id,
            name,
            requires_avr,
            requires_headset
        )

        result = database.execute_single(base_query, params)

        if result['success']:
            initialize_equipment_set_components(set_id, data)
            added_sets.append(name)
        else:
            failed_sets.append({
                "name": name,
                "error": result.get("error", "Unknown error")
            })

    # Generate response summary
    if failed_sets:
        return common_error_response(
            message=f"Added {len(added_sets)} equipment sets successfully, "
                    f"but {len(failed_sets)} failed.",
            data={"added": added_sets, "failed": failed_sets}
        )

    return common_success_response(
        data={"added": added_sets},
        message=f"Successfully added {len(added_sets)} equipment sets."
    )


@bp_equipment_sets.route("/<id>", methods=["PUT"])
@require_access('admin')
def edit(id):
    # Validate JSON payload
    data, error_response = check_json_payload()
    if error_response:
        return error_response

    # fetch data forms
    location_id = data['location_id']
    name = data['name']

    requires_avr = "true" if data.get('requires_avr') else "false"
    requires_headset = "true" if data.get('requires_headset') else "false"

    plugged_power_cable =  "true" if data.get('plugged_power_cable') else "false"
    plugged_display_cable =  "true" if data.get('plugged_display_cable') else "false"

    connectivity = data.get('connectivity', 'untested')
    performance = data.get('performance', 'untested')

    status = data.get('status', 'active')
    issue = data.get('issue', '')
    

    if any(item is None for item in [location_id, name, requires_avr, requires_headset, plugged_display_cable, plugged_power_cable, connectivity, performance, status]):
        return jsonify({
            "msg": "forms data incomplete"
        }), 400

    # prepare query and parameters
    base_query = """
        update equipment_sets set
            equipment_sets.location_id = %s,
            equipment_sets.name = %s,
            equipment_sets.requires_avr = %s,
            equipment_sets.requires_headset = %s,
            equipment_sets.plugged_power_cable = %s,
            equipment_sets.plugged_display_cable = %s,
            equipment_sets.connectivity = %s,
            equipment_sets.performance = %s,
            equipment_sets.status = %s,
            equipment_sets.issue = %s
        
        where
            equipment_sets.id = %s
    """

    base_params = (
        location_id,
        name,
        requires_avr,
        requires_headset,
        plugged_power_cable,
        plugged_display_cable,
        connectivity,
        performance,
        status,
        issue,
        id    
    )

    equipment_set_updated = database.execute_single(base_query, base_params)

    if not equipment_set_updated['success']:
        return common_database_error_response(equipment_set_updated)

    return common_success_response(
        data=True,
        message="Updated Equipment Set"
    )


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

