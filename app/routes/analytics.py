from flask import Blueprint, jsonify, request
from .. services import database
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from ..config import config
from datetime import datetime, timedelta
from ..services.validation import check_json_payload, check_required_fields, check_order_parameter, common_success_response, common_error_response, common_database_error_response

bp_analytics = Blueprint("analytics", __name__)

@bp_analytics.route("/line/account-logins/week", methods=["GET"])
def account_logins_week():
    start_date = (datetime.now() - timedelta(days=6)).date()

    query = f"""
        SELECT 
            DATE(created_at) AS day,
            COUNT(*) AS logins
        FROM account_logs
        WHERE action = 'login'
          AND DATE(created_at) >= '{start_date}'
        GROUP BY DATE(created_at)
        ORDER BY DATE(created_at)
    """

    results = database.fetch_all(query)
    if not results or "data" not in results:
        return common_error_response("Result not found")

    labels = [r["day"].strftime("%a") for r in results["data"]]
    data = [r["logins"] for r in results["data"]]

    return common_success_response(data={
        "labels": labels,
        "datasets": [{
            "label": "Account Logins",
            "data": data,
            "borderColor": "rgba(75,192,192,1)",
            "fill": False,
            "tension": 0.3
        }]
    })


@bp_analytics.route("/line/account-activities/week", methods=["GET"])
def account_activities_week():
    start_date = (datetime.now() - timedelta(days=6)).date()

    query = f"""
        SELECT 
            DATE(created_at) AS day,
            COUNT(*) AS activities
        FROM account_logs
        WHERE DATE(created_at) >= '{start_date}'
        GROUP BY DATE(created_at)
        ORDER BY DATE(created_at)
    """

    results = database.fetch_all(query)
    if not results or "data" not in results:
        return common_error_response("Result not found")

    labels = [r["day"].strftime("%a") for r in results["data"]]
    data = [r["activities"] for r in results["data"]]

    return common_success_response(data={
        "labels": labels,
        "datasets": [{
            "label": "Account Activities",
            "data": data,
            "borderColor": "rgba(255,99,132,1)",
            "fill": False,
            "tension": 0.3
        }]
    })


@bp_analytics.route("/line/equipment-activities/week", methods=["GET"])
def equipment_activities_week():
    start_date = (datetime.now() - timedelta(days=6)).date()

    query = f"""
        SELECT 
            DATE(created_at) AS day,
            COUNT(*) AS activities
        FROM equipment_set_activity
        WHERE DATE(created_at) >= '{start_date}'
        GROUP BY DATE(created_at)
        ORDER BY DATE(created_at)
    """

    results = database.fetch_all(query)
    if not results or "data" not in results:
        return common_error_response("Result not found")

    labels = [r["day"].strftime("%a") for r in results["data"]]
    data = [r["activities"] for r in results["data"]]

    return common_success_response(data={
        "labels": labels,
        "datasets": [{
            "label": "Equipment Activities",
            "data": data,
            "borderColor": "rgba(75,192,192,1)",
            "fill": False,
            "tension": 0.3
        }]
    })


@bp_analytics.route("/bar/equipment-activities/daily", methods=["GET"])
def equipment_activities_daily():
    start_date = (datetime.now() - timedelta(days=6)).date()

    query = f"""
        SELECT 
            DATE(created_at) AS day,
            COUNT(*) AS total_updates
        FROM equipment_set_activity
        WHERE DATE(created_at) >= '{start_date}'
        GROUP BY DATE(created_at)
        ORDER BY DATE(created_at)
    """

    results = database.fetch_all(query)
    if not results or "data" not in results:
        return common_error_response("Result not found")

    labels = [r["day"].strftime("%a") for r in results["data"]]
    data = [r["total_updates"] for r in results["data"]]

    return common_success_response(data={
        "labels": labels,
        "datasets": [{
            "label": "Equipment Updates",
            "data": data,
            "backgroundColor": "rgba(75, 192, 192, 0.5)"
        }]
    })


@bp_analytics.route("/bar/equipment/location", methods=["GET"])
def equipment_per_location():
    query = """
        SELECT 
            l.name AS location,
            COUNT(e.id) AS total
        FROM equipment_sets e
        JOIN locations l ON l.id = e.location_id
        GROUP BY l.id
        ORDER BY l.name
    """

    results = database.fetch_all(query)
    if not results or "data" not in results:
        return common_error_response("Result not found")

    labels = [r["location"] for r in results["data"]]
    data = [r["total"] for r in results["data"]]

    return common_success_response(data={
        "labels": labels,
        "datasets": [{
            "label": "Equipment per Location",
            "data": data,
            "backgroundColor": "rgba(153, 102, 255, 0.6)"
        }]
    })


@bp_analytics.route("/pie/equipment/issues-ratio", methods=["GET"])
def equipment_issues_ratio():
    query = """
        SELECT
            COUNT(DISTINCT es.id) AS total_equipment_sets,
            COUNT(DISTINCT CASE
                WHEN 
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
                THEN es.id
            END) AS equipment_sets_with_issues
        FROM equipment_sets AS es
        LEFT JOIN equipment_set_components AS esc
            ON es.id = esc.equipment_set_id;
    """

    result = database.fetch_one(query)
    
    if not result or "data" not in result or not result["data"]:
        return common_error_response("Result not found")

    data_row = result["data"]
    total = data_row.get("total_equipment_sets", 0)
    with_issue = data_row.get("equipment_sets_with_issues", 0)
    complete = total - with_issue
    ratio = round(with_issue / total, 2) if total > 0 else 0.0

    return common_success_response(data={
        "labels": ["With Issues", "Complete"],
        "datasets": [{
            "label": "Equipment Status",
            "data": [with_issue, complete],
            "backgroundColor": ["#B31F3F", "#366FEB"]
        }],
        "summary": {
            "total_equipment_sets": total,
            "ratio_with_issues": ratio
        }
    })