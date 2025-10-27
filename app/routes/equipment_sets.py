from flask import Blueprint, jsonify, request
from ..services.jwt import require_access
from ..services.security import generate_id
from ..services import database
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..config import config
from .equipment_set_components import initialize_equipment_set_components
from .equipment_set_activity import log_equipment_set_changes
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
            locations.name as location_name,
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
        join locations on eq_set.location_id = locations.id
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
    base_query += f"ORDER BY CAST(REGEXP_REPLACE(eq_set.name, '[^0-9]', '') AS UNSIGNED);"
    

    # closing statements
    base_query += ";"

    # execute query
    equipment_set_fetch = database.fetch_all(base_query, tuple(conditional_params))

    # query fails
    if not equipment_set_fetch['success']:
        return common_database_error_response(equipment_set_fetch)

    # success
    return common_success_response(equipment_set_fetch['data'])


@bp_equipment_sets.route("/location/<location_id>", methods=["GET"])
@jwt_required()
@require_access("guest")
def get_full_location(location_id):
    # setup base query
    base_query = """
        SELECT
            eq_set.id AS equipment_set_id,
            eq_set.name AS equipment_set_name,
            eq_set.location_id,
            loc.name AS location_name,

            eq_set.requires_avr,
            eq_set.requires_headset,

            eq_set.plugged_power_cable,
            eq_set.plugged_display_cable,

            eq_set.connectivity,
            eq_set.performance,
            eq_set.status,
            eq_set.issue,

            eq_set.created_at AS set_created_at,
            eq_set.updated_at AS set_updated_at,

            eq_set_comp.system_unit_name,
            eq_set_comp.system_unit_serial_number,
            eq_set_comp.monitor_name,
            eq_set_comp.monitor_serial_number,
            eq_set_comp.keyboard_name,
            eq_set_comp.keyboard_serial_number,
            eq_set_comp.mouse_name,
            eq_set_comp.mouse_serial_number,
            eq_set_comp.avr_name,
            eq_set_comp.avr_serial_number,
            eq_set_comp.headset_name,
            eq_set_comp.headset_serial_number,
            eq_set_comp.updated_at AS components_updated_at

        FROM equipment_sets AS eq_set
        JOIN locations AS loc ON eq_set.location_id = loc.id
        LEFT JOIN equipment_set_components AS eq_set_comp
            ON eq_set.id = eq_set_comp.equipment_set_id
        WHERE eq_set.location_id = %s
        ORDER BY CAST(REGEXP_REPLACE(eq_set.name, '[^0-9]', '') AS UNSIGNED);
    """

    equipment_set_full_fetch = database.fetch_all(base_query, (location_id, ))

    if not equipment_set_full_fetch['success']:
        return common_database_error_response(equipment_set_full_fetch)

    return common_success_response(equipment_set_full_fetch['data'])


@bp_equipment_sets.route("/single", methods=["POST"])
@jwt_required()
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
@jwt_required()
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

    query_fetch_latest_num = """
        SELECT COUNT(*) AS total_count
        FROM equipment_sets
        WHERE equipment_sets.location_id = %s;
    """

    highest = database.fetch_scalar(query_fetch_latest_num, (location_id, ))['data']

    # Loop to add multiple equipment sets
    for i in range(highest+1, highest + count + 1):
        name = f"{prefix}{i}"
        set_id = generate_id()

        print(name)

        params = (
            set_id,
            location_id,
            name,
            requires_avr,
            requires_headset
        )

        result = database.execute_single(base_query, params)

        if result['success']:
            if initialize_equipment_set_components(set_id, data):
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

    requires_avr = data.get('requires_avr')
    requires_headset = data.get('requires_headset')

    plugged_power_cable =  data.get('plugged_power_cable')
    plugged_display_cable = data.get('plugged_display_cable')

    connectivity = data.get('connectivity')
    performance = data.get('performance')

    status = data.get('status')
    issue = data.get('issue', '')
    

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
    
    old_data_fetched, old_data = fetch_equipment_sets(id)

    equipment_set_updated = database.execute_single(base_query, base_params)

    new_data_fetched, new_data = fetch_equipment_sets(id)

    if not equipment_set_updated['success']:
        return common_database_error_response(equipment_set_updated)
    
    if old_data_fetched and new_data_fetched and equipment_set_updated['success']:
        account_id = get_jwt_identity()
        logging = log_equipment_set_changes(account_id, id, old_data, new_data)

        if(logging['success']):
            print("Logging Complete", "- "*50)
    else:
        print("Logging Failed", "! "*50)

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


def fetch_equipment_sets(id: str):
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
            eq_set.issue
        from equipment_sets as eq_set
        where eq_set.id = %s;
    """

    # execute query
    equipment_set_fetch = database.fetch_one(base_query, (id, ))

    # query fails
    if not equipment_set_fetch['success']:
        return False, None

    # success
    return True, equipment_set_fetch['data']


# ANALYTICSSSSS ==================================================================

@bp_equipment_sets.route("/analytics/total", methods=["GET"])
def analytics_total():
    query = """
        SELECT COUNT(id) AS data
        FROM equipment_sets;
    """

    # execute query
    equipment_sets_analytics_fetch_total = database.fetch_scalar(query)

    # query fails
    if not equipment_sets_analytics_fetch_total['success']:
        return common_database_error_response(equipment_sets_analytics_fetch_total)
    
    print(equipment_sets_analytics_fetch_total)

    # success
    return common_success_response(data=equipment_sets_analytics_fetch_total['data'])

@bp_equipment_sets.route("/analytics/total/location/<location_id>", methods=["GET"])
def analytics_total_per_location(location_id):
    query = """
        SELECT COUNT(id) AS data
        FROM equipment_sets
        WHERE location_id = %s;
    """

    # execute query
    equipment_sets_analytics_fetch_total_per_location = database.fetch_scalar(query, (location_id, ))

    # query fails
    if not equipment_sets_analytics_fetch_total_per_location['success']:
        return common_database_error_response(equipment_sets_analytics_fetch_total_per_location)
    
    # success
    return common_success_response(equipment_sets_analytics_fetch_total_per_location['data'])


@bp_equipment_sets.route("/analytics/ratio", methods=["GET"])
def analytics_ratio_issues():
    query = """
        SELECT
            (SELECT COUNT(id) FROM equipment_sets) AS total,

            (
                SELECT COUNT(DISTINCT es.id)
                FROM equipment_sets AS es
                LEFT JOIN equipment_set_components AS esc 
                    ON es.id = esc.equipment_set_id
                WHERE 
                    -- Missing component name or serial
                    (
                        esc.system_unit_name IS NULL OR esc.system_unit_name = '' OR
                        esc.system_unit_serial_number IS NULL OR esc.system_unit_serial_number = '' OR
                        esc.monitor_name IS NULL OR esc.monitor_name = '' OR
                        esc.monitor_serial_number IS NULL OR esc.monitor_serial_number = '' OR
                        esc.keyboard_name IS NULL OR esc.keyboard_name = '' OR
                        esc.keyboard_serial_number IS NULL OR esc.keyboard_serial_number = '' OR
                        esc.mouse_name IS NULL OR esc.mouse_name = '' OR
                        esc.mouse_serial_number IS NULL OR esc.mouse_serial_number = '' OR
                        esc.avr_name IS NULL OR esc.avr_name = '' OR
                        esc.avr_serial_number IS NULL OR esc.avr_serial_number = '' OR
                        esc.headset_name IS NULL OR esc.headset_name = '' OR
                        esc.headset_serial_number IS NULL OR esc.headset_serial_number = ''
                    )
                    OR es.plugged_power_cable = FALSE
                    OR es.plugged_display_cable = FALSE
                    OR es.performance = 'unstable'
                    OR es.connectivity = 'unstable'
                    OR (es.issue IS NOT NULL AND es.issue <> '')
            ) AS issues;
    """

    # execute query
    equipment_sets_analytics_fetch_ratio_issues = database.fetch_one(query)

    # query fails
    if not equipment_sets_analytics_fetch_ratio_issues['success']:
        return common_database_error_response(equipment_sets_analytics_fetch_ratio_issues)
    
    # success
    return common_success_response(equipment_sets_analytics_fetch_ratio_issues['data'])


@bp_equipment_sets.route("/analytics/issues/total", methods=["GET"])
def analytics_issues_total():
    query = """
        SELECT COUNT(DISTINCT es.id) AS equipment_sets_with_issues
        FROM equipment_sets AS es
        LEFT JOIN equipment_set_components AS esc
            ON es.id = esc.equipment_set_id
        WHERE 
            -- Basic equipment set issue conditions
            es.plugged_power_cable = 'false'
            OR es.plugged_display_cable = 'false'
            OR es.connectivity = 'unstable'
            OR es.performance = 'unstable'
            OR es.status = 'maintenance'
            OR es.issue IS NOT NULL
            -- Component-based issues
            OR (
                (esc.system_unit_name IS NULL OR esc.system_unit_name = '' 
                OR esc.system_unit_serial_number IS NULL OR esc.system_unit_serial_number = '')
                OR (esc.monitor_name IS NULL OR esc.monitor_name = '' 
                OR esc.monitor_serial_number IS NULL OR esc.monitor_serial_number = '')
                OR (esc.keyboard_name IS NULL OR esc.keyboard_name = '' 
                OR esc.keyboard_serial_number IS NULL OR esc.keyboard_serial_number = '')
                OR (esc.mouse_name IS NULL OR esc.mouse_name = '' 
                OR esc.mouse_serial_number IS NULL OR esc.mouse_serial_number = '')
                OR (es.requires_avr = TRUE AND (esc.avr_name IS NULL OR esc.avr_name = '' 
                OR esc.avr_serial_number IS NULL OR esc.avr_serial_number = ''))
                OR (es.requires_headset = TRUE AND (esc.headset_name IS NULL OR esc.headset_name = '' 
                OR esc.headset_serial_number IS NULL OR esc.headset_serial_number = ''))
            );
    """

    # execute query
    equipment_sets_analytics_fetch_issues_total = database.fetch_scalar(query)

    # query fails
    if not equipment_sets_analytics_fetch_issues_total['success']:
        return common_database_error_response(equipment_sets_analytics_fetch_issues_total)
    
    # success
    return common_success_response(equipment_sets_analytics_fetch_issues_total['data'])



@bp_equipment_sets.route("/analytics/issues/total/location/<id>", methods=["GET"])
def analytics_issues_total_location(id):
    query = """
        SELECT COUNT(DISTINCT es.id) AS equipment_sets_with_issues
        FROM equipment_sets AS es
        LEFT JOIN equipment_set_components AS esc
            ON es.id = esc.equipment_set_id
        WHERE 
            es.location_id = %s
            AND (
                es.plugged_power_cable = FALSE
                OR es.plugged_display_cable = FALSE
                OR es.connectivity = 'unstable'
                OR es.performance = 'unstable'
                OR es.status = 'maintenance'
                OR es.issue IS NOT NULL
                OR (
                    esc.system_unit_name IS NULL OR esc.system_unit_name = '' 
                    OR esc.system_unit_serial_number IS NULL OR esc.system_unit_serial_number = ''
                    OR esc.monitor_name IS NULL OR esc.monitor_name = '' 
                    OR esc.monitor_serial_number IS NULL OR esc.monitor_serial_number = ''
                    OR esc.keyboard_name IS NULL OR esc.keyboard_name = '' 
                    OR esc.keyboard_serial_number IS NULL OR esc.keyboard_serial_number = ''
                    OR esc.mouse_name IS NULL OR esc.mouse_name = '' 
                    OR esc.mouse_serial_number IS NULL OR esc.mouse_serial_number = ''
                    OR (es.requires_avr = TRUE AND (esc.avr_name IS NULL OR esc.avr_name = '' OR esc.avr_serial_number IS NULL OR esc.avr_serial_number = ''))
                    OR (es.requires_headset = TRUE AND (esc.headset_name IS NULL OR esc.headset_name = '' OR esc.headset_serial_number IS NULL OR esc.headset_serial_number = ''))
                )
            );

    """

    # execute query
    equipment_sets_analytics_fetch_issues_total_location = database.fetch_scalar(query, (id, ))

    # query fails
    if not equipment_sets_analytics_fetch_issues_total_location['success']:
        return common_database_error_response(equipment_sets_analytics_fetch_issues_total_location)
    
    # success
    return common_success_response(equipment_sets_analytics_fetch_issues_total_location['data'])