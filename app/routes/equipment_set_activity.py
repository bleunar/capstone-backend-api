from flask import Blueprint, request
from ..services import database
from flask_jwt_extended import jwt_required
from ..services.validation import common_success_response, common_error_response, common_database_error_response, check_json_payload

bp_equipment_set_activity = Blueprint("equipment_set_activity", __name__)

@bp_equipment_set_activity.route("/", methods=["GET"])
@jwt_required()
def get_equipment_set_activities():
    base_query = """
        SELECT 
            eqsa.id AS id,
            eqsa.action,
            eqsa.value,
            eqsa.status,
            eqsa.created_at,
            a.username AS performed_by_username,
            a.id AS performed_by_id,
            es.name AS equipment_set_name,
            es.id AS equipment_set_id,
            l.name AS location_name,
            l.id AS location_id
        FROM equipment_set_activity AS eqsa
        JOIN accounts AS a ON eqsa.performed_by_account_id = a.id
        JOIN equipment_sets AS es ON eqsa.equipment_set_id = es.id
        JOIN locations AS l ON es.location_id = l.id
    """

    # --- CONDITIONALS ---
    conditional_query = []
    conditional_params = {}

    # Optional filters
    if 'id' in request.args and request.args.get('id'):
        conditional_query.append("eqsa.id = :id")
        conditional_params['id'] = request.args.get('id')

    if 'account_id' in request.args and request.args.get('account_id'):
        conditional_query.append("eqsa.performed_by_account_id = :account_id")
        conditional_params['account_id'] = request.args.get('account_id')

    if 'equipment_set_id' in request.args and request.args.get('equipment_set_id'):
        conditional_query.append("eqsa.equipment_set_id = :equipment_set_id")
        conditional_params['equipment_set_id'] = request.args.get('equipment_set_id')

    if 'location_id' in request.args and request.args.get('location_id'):
        conditional_query.append("l.id = :location_id")
        conditional_params['location_id'] = request.args.get('location_id')

    # --- Date filtering ---
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if start_date and end_date:
        conditional_query.append("eqsa.created_at BETWEEN :start_date AND :end_date")
        conditional_params['start_date'] = start_date
        conditional_params['end_date'] = end_date
    elif start_date:
        conditional_query.append("eqsa.created_at >= :start_date")
        conditional_params['start_date'] = start_date
    elif end_date:
        conditional_query.append("eqsa.created_at <= :end_date")
        conditional_params['end_date'] = end_date

    # --- Build WHERE clause ---
    if conditional_query:
        base_query += " WHERE " + " AND ".join(conditional_query)

    # --- Sort and finalize ---
    base_query += " ORDER BY eqsa.created_at DESC;"

    # --- Execute query ---
    equipment_set_fetch = database.fetch_all(base_query, conditional_params)

    if not equipment_set_fetch['success']:
        return common_database_error_response(equipment_set_fetch)

    return common_success_response(equipment_set_fetch['data'])



@bp_equipment_set_activity.route("/clear", methods=["POST"])
def clear_activities():

    data, error_response = check_json_payload()
    if error_response:
        return error_response
    
    activity_list = data.get("cleared_activities", [])

    if not activity_list:
        return common_error_response(
            message="No Activities Provided"
        )

    # generate placeholders for each ID
    placeholders = ", ".join(["%s"] * len(activity_list))

    query = f"""
        UPDATE equipment_set_activity
        SET
            status = 'emailed',
            emailed_at = CURRENT_TIMESTAMP
        WHERE id IN ({placeholders})
    """

    result = database.execute_single(query, tuple(activity_list))

    if not result["success"]:
        return common_database_error_response(result)

    return common_success_response(
        data=True
    )



@bp_equipment_set_activity.route("/today/<location_id>", methods=["GET"])
def get_today_logged_activities(location_id):
    query = """
        SELECT 
            eqsa.id AS id,
            eqsa.action,
            eqsa.value AS current_value,
            emailed_prev.value AS previous_value,
            eqsa.status,
            eqsa.created_at,
            a.username AS performed_by_username,
            CONCAT(
                a.first_name,
                IF(a.middle_name IS NOT NULL AND a.middle_name != '', CONCAT(' ', a.middle_name), ''),
                ' ',
                a.last_name
            ) AS performed_by_full_name,
            a.id AS performed_by_id,
            es.name AS equipment_set_name,
            es.id AS equipment_set_id,
            l.name AS location_name,
            l.id AS location_id
        FROM equipment_set_activity AS eqsa
        JOIN accounts AS a 
            ON eqsa.performed_by_account_id = a.id
        JOIN equipment_sets AS es 
            ON eqsa.equipment_set_id = es.id
        JOIN locations AS l 
            ON es.location_id = l.id
        LEFT JOIN equipment_set_activity AS emailed_prev 
            ON emailed_prev.id = (
                SELECT ep2.id
                FROM equipment_set_activity AS ep2
                WHERE 
                    ep2.equipment_set_id = eqsa.equipment_set_id
                    AND ep2.action = eqsa.action
                    AND ep2.status = 'emailed'
                    AND ep2.created_at < eqsa.created_at
                ORDER BY ep2.created_at DESC, ep2.id DESC
                LIMIT 1
            )
        WHERE 
            eqsa.id IN (
                SELECT MAX(sub.id)
                FROM equipment_set_activity AS sub
                WHERE sub.status <> 'emailed'
                GROUP BY sub.equipment_set_id, sub.action
            )
            AND (
                emailed_prev.value IS NULL  -- no previous emailed record
                OR eqsa.value <> emailed_prev.value  -- value changed since last emailed
            )
            AND DATE(eqsa.created_at) = CURDATE()
            AND l.id = %s
        ORDER BY eqsa.created_at DESC;
    """


    result = database.fetch_all(query, (location_id,))

    if not result["success"]:
        return common_database_error_response(result)

    return common_success_response(result["data"])


# ================================================== Helper Functions

def log_equipment_set_changes(account_id: str, equipment_set_id: str, old: dict, new: dict):

    logs = []
    log_types = [
        'name'
        'system_unit_name',
        'monitor_name',
        'keyboard_name',
        'mouse_name',
        'avr_name',
        'headset_name',
        'system_unit_serial',
        'monitor_serial',
        'keyboard_serial',
        'mouse_serial',
        'avr_serial',
        'headset_serial',
        'requires_avr',
        'requires_headset',
        'plugged_display_cable',
        'plugged_power_cable',
        'connectivity',
        'performance',
        'issue',
        'status'
    ]
    updates = get_updates(old, new)
    print(updates)

    for key, value in updates:
        if key not in log_types:
            print("> ERROR LOG TYPE ISSUE")
        logs.append(("insert into equipment_set_activity (performed_by_account_id, equipment_set_id, action, value) values (%s, %s, %s, %s)", (account_id, equipment_set_id, key, value)))

    return log_to_database(logs)

def log_equipment_component(data):
    pass
    

def log_to_database(logs: list) -> bool:
    return database.execute_transaction(logs)


def get_updates(old_data: dict, new_data: dict):
    updated = []
    for key, new_value in new_data.items():
        old_value = old_data.get(key)
        if old_value != new_value:
            updated.append((key, new_value))
    return updated
