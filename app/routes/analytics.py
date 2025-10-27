from flask import Blueprint, jsonify, request
from .. services import database
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from ..config import config
from ..services.validation import check_json_payload, check_required_fields, check_order_parameter, common_success_response, common_error_response, common_database_error_response

bp_analytics = Blueprint("analytics", __name__)

@bp_analytics.route("/line")
@jwt_required()
def get_line_data():
    query_name = request.args.get("q") # get the value from the 'q' parameter

    # check if value exists, return proper response
    if not query_name:
        return common_error_response(
            message="Missing query parameter ?q="
        )

    # execute the query corresponding to the value
    result, error = executie(f"line_{query_name}")

    # if error, return proper response
    if error:
        return common_error_response(
            message=error
        )

    # if success, celebrate
    return common_success_response(
        data=format_for_chartjs(result)
    )
    


@bp_analytics.route("/bar")
@jwt_required()
def get_bar_data():
    query_name = request.args.get("q")
    if not query_name:
        return common_error_response(
            message="Missing query parameter ?q="
        )

    result, error = executie(f"bar_{query_name}")
    if error:
        return common_error_response(
            message=error
        )

    return common_success_response(
        data=format_for_chartjs(result)
    )


@bp_analytics.route("/pie")
@jwt_required()
def get_pie_data():
    query_name = request.args.get("q")
    if not query_name:
        return common_error_response(
            message="Missing query parameter ?q="
        )

    result, error = executie(f"pie_{query_name}")
    if error:
        return common_error_response(
            message=error
        )

    return common_success_response(
        data=format_for_chartjs(result)
    )


@bp_analytics.route("/count")
@jwt_required()
def get_count_data():
    query_name = request.args.get("q")
    if not query_name:
        return common_error_response(
            message="Missing query parameter ?q="
        )

    result, error = executie(f"count_{query_name}")
    if error:
        return common_error_response(
            message=error
        )

    # fetches the data and takes the a 
    total = result['data']
    return common_success_response(
        data=total
    )

# ================================================== Queries 

ANALYTICS_QUERIES = {
    # === LINE CHARTS ===
    "line_logins": """
        SELECT DATE(created_at) AS date, COUNT(id) AS total
        FROM account_logs
        WHERE action = 'login'
          AND created_at >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
        GROUP BY DATE(created_at)
        ORDER BY DATE(created_at) ASC;
    """,

    "line_account_activity_week": """
        SELECT DATE(created_at) AS date, COUNT(id) AS total
        FROM equipment_set_activity
        WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
        GROUP BY DATE(created_at)
        ORDER BY DATE(created_at) ASC;
    """,


    # === BAR CHARTS ===
    "bar_equipment_activity_daily": """
        SELECT DATE(created_at) AS date, COUNT(id) AS total
        FROM equipment_set_activity
        WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
        GROUP BY DATE(created_at)
        ORDER BY DATE(created_at) ASC;
    """,

    "bar_equipment_per_location": """
        SELECT l.name AS label, COUNT(es.id) AS total
        FROM equipment_sets es
        JOIN locations l ON l.id = es.location_id
        GROUP BY l.id
        ORDER BY l.name ASC;
    """,


    # === PIE CHARTS ===
    "pie_equipment_issue_ratio": """
        SELECT 
            CASE 
                WHEN issue IS NULL OR issue = '' THEN 'No Issues'
                ELSE 'With Issues'
            END AS label,
            COUNT(id) AS total
        FROM equipment_sets
        GROUP BY label;
    """,


    # === COUNTS ===
    "count_accounts_total": """
        SELECT COUNT(id) AS data
        FROM accounts;
    """,

    "count_accounts_active": """
        SELECT COUNT(DISTINCT account_id) AS total
        FROM account_logs
        WHERE action = 'login'
          AND created_at >= NOW() - INTERVAL 1 HOUR;
    """,

    "count_accounts_activity_today": """
        SELECT COUNT(DISTINCT performed_by_account_id) AS total
        FROM equipment_set_activity
        WHERE DATE(created_at) = CURDATE();
    """,

    "count_equipment_total": """
        SELECT COUNT(id) AS total
        FROM equipment_sets;
    """,

    "count_equipment_with_issues": """
        SELECT 
            COUNT(DISTINCT es.id) AS problematic_equipment_count
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
            OR (es.issue IS NOT NULL AND es.issue <> '');
    """,

    "count_equipment_activity_today": """
        SELECT COUNT(DISTINCT equipment_set_id) AS total
        FROM equipment_set_activity
        WHERE DATE(created_at) = CURDATE();
    """,
}

# ================================================== HELPER FUNCTIONS 

# execute query based on named queries
def executie(query_name):
    query = ANALYTICS_QUERIES.get(query_name)
    if not query:
        return None, f"invalid key: {query_name}"
    try:
        # use fetch_scalar for count queries, fetch_all for others
        if query_name.startswith("count_"):
            result = database.fetch_scalar(query)
        else:
            result = database.fetch_all(query)
        return result, None
    except Exception as e:
        return None, str(e)


# chart js formatter
def format_for_chartjs(data, label_field="label", value_field="total"):
    if not data:
        return {"labels": [], "data": []}
    
    print(type(data))
    return {
        "labels": [row.get(label_field) or row.get("date") for row in data['data']],
        "data": [row.get(value_field, 0) for row in data['data']]
    }
