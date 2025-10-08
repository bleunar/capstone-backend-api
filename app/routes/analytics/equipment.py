"""
Analytics routes for equipment-related data and visualizations.
"""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from ...services.jwt import require_access
from ...services import database
from ...services.validation import common_database_error_response
from .utils import (
    format_pie_chart_data, format_bar_chart_data, format_line_chart_data,
    get_date_range_filter, get_time_series_data, format_analytics_response
)

bp_analytics_equipment = Blueprint("analytics_equipment", __name__)


@bp_analytics_equipment.route("/status", methods=["GET"])
@jwt_required()
@require_access("guest")
def get_equipment_status():
    
    chart_type = request.args.get('chart_type', 'pie')
    location_filter = request.args.get('location_id')
    
    # Query for equipment status distribution
    query = """
        SELECT 
            eq.status as label,
            COUNT(*) as count
        FROM equipment_sets eq
        WHERE 1=1
    """
    
    params = []
    
    # Add location filter if provided
    if location_filter:
        query += " AND eq.location_id = %s"
        params.append(location_filter)
    
    query += " GROUP BY eq.status ORDER BY count DESC"
    
    # Execute query
    result = database.fetch_all(query, tuple(params))
    
    if not result['success']:
        return common_database_error_response(result)
    
    data = result['data']
    
    # Format chart data
    chart_data = None
    if chart_type == 'pie':
        chart_data = format_pie_chart_data(data, 'label', 'count')
    elif chart_type == 'bar':
        chart_data = format_bar_chart_data(data, 'label', 'count', 'Equipment Status')
    elif chart_type == 'doughnut':
        from .utils import format_doughnut_chart_data
        chart_data = format_doughnut_chart_data(data, 'label', 'count')
    
    # Calculate metadata
    total_equipment = sum(item['count'] for item in data)
    metadata = {
        'total_equipment': total_equipment,
        'location_filter': location_filter
    }
    
    return format_analytics_response(data, chart_data, metadata), 200


@bp_analytics_equipment.route("/functionality", methods=["GET"])
@jwt_required()
@require_access("guest")
def get_equipment_functionality():
    
    chart_type = request.args.get('chart_type', 'pie')
    location_filter = request.args.get('location_id')
    
    # Query for equipment functionality
    query = """
        SELECT 
            eq.functionability as label,
            COUNT(*) as count
        FROM equipment_sets eq
        WHERE 1=1
    """
    
    params = []
    
    if location_filter:
        query += " AND eq.location_id = %s"
        params.append(location_filter)
    
    query += " GROUP BY eq.functionability ORDER BY count DESC"
    
    # Execute query
    result = database.fetch_all(query, tuple(params))
    
    if not result['success']:
        return common_database_error_response(result)
    
    data = result['data']
    
    # Format chart data
    chart_data = None
    if chart_type == 'pie':
        chart_data = format_pie_chart_data(data, 'label', 'count')
    elif chart_type == 'bar':
        chart_data = format_bar_chart_data(data, 'label', 'count', 'Equipment Functionality')
    
    metadata = {
        'total_equipment': sum(item['count'] for item in data),
        'location_filter': location_filter
    }
    
    return format_analytics_response(data, chart_data, metadata), 200


@bp_analytics_equipment.route("/by-location", methods=["GET"])
@jwt_required()
@require_access("guest")
def get_equipment_by_location():
    
    chart_type = request.args.get('chart_type', 'bar')
    status_filter = request.args.get('status')
    
    # Query for equipment by location
    query = """
        SELECT 
            l.name as label,
            COUNT(eq.id) as count
        FROM locations l
        LEFT JOIN equipment_sets eq ON l.id = eq.location_id
        WHERE 1=1
    """
    
    params = []
    
    if status_filter:
        query += " AND eq.status = %s"
        params.append(status_filter)
    
    query += " GROUP BY l.id, l.name ORDER BY count DESC"
    
    # Execute query
    result = database.fetch_all(query, tuple(params))
    
    if not result['success']:
        return common_database_error_response(result)
    
    data = result['data']
    
    # Format chart data
    chart_data = None
    if chart_type == 'bar':
        chart_data = format_bar_chart_data(data, 'label', 'count', 'Equipment by Location')
    elif chart_type == 'pie':
        chart_data = format_pie_chart_data(data, 'label', 'count')
    
    metadata = {
        'total_equipment': sum(item['count'] for item in data),
        'status_filter': status_filter
    }
    
    return format_analytics_response(data, chart_data, metadata), 200


@bp_analytics_equipment.route("/requirements", methods=["GET"])
@jwt_required()
@require_access("guest")
def get_equipment_requirements():
    
    # Query for equipment requirements
    query = """
        SELECT 
            'AVR Required' as requirement,
            SUM(CASE WHEN requires_avr = 1 THEN 1 ELSE 0 END) as required_count,
            SUM(CASE WHEN requires_avr = 0 THEN 1 ELSE 0 END) as not_required_count
        FROM equipment_sets
        UNION ALL
        SELECT 
            'Headset Required' as requirement,
            SUM(CASE WHEN requires_headset = 1 THEN 1 ELSE 0 END) as required_count,
            SUM(CASE WHEN requires_headset = 0 THEN 1 ELSE 0 END) as not_required_count
        FROM equipment_sets
        UNION ALL
        SELECT 
            'Camera Required' as requirement,
            SUM(CASE WHEN requires_camera = 1 THEN 1 ELSE 0 END) as required_count,
            SUM(CASE WHEN requires_camera = 0 THEN 1 ELSE 0 END) as not_required_count
        FROM equipment_sets
    """
    
    # Execute query
    result = database.fetch_all(query)
    
    if not result['success']:
        return common_database_error_response(result)
    
    data = result['data']
    
    # Transform data for better visualization
    chart_data_list = []
    for item in data:
        chart_data_list.extend([
            {'label': f"{item['requirement']} - Yes", 'count': item['required_count']},
            {'label': f"{item['requirement']} - No", 'count': item['not_required_count']}
        ])
    
    # Format as bar chart
    chart_data = format_bar_chart_data(chart_data_list, 'label', 'count', 'Equipment Requirements')
    
    metadata = {
        'requirements_analyzed': len(data)
    }
    
    return format_analytics_response(data, chart_data, metadata), 200


@bp_analytics_equipment.route("/connectivity", methods=["GET"])
@jwt_required()
@require_access("guest")
def get_equipment_connectivity():
    
    chart_type = request.args.get('chart_type', 'pie')
    
    # Query for connectivity analysis
    query = """
        SELECT 
            CASE 
                WHEN internet_connectivity = 1 AND plugged_power_cable = 1 AND plugged_display_cable = 1 
                THEN 'Fully Connected'
                WHEN internet_connectivity = 1 
                THEN 'Internet Only'
                WHEN plugged_power_cable = 1 AND plugged_display_cable = 1 
                THEN 'Cables Only'
                WHEN plugged_power_cable = 1 OR plugged_display_cable = 1 OR internet_connectivity = 1
                THEN 'Partially Connected'
                ELSE 'Not Connected'
            END as label,
            COUNT(*) as count
        FROM equipment_sets
        GROUP BY label
        ORDER BY count DESC
    """
    
    # Execute query
    result = database.fetch_all(query)
    
    if not result['success']:
        return common_database_error_response(result)
    
    data = result['data']
    
    # Format chart data
    chart_data = None
    if chart_type == 'pie':
        chart_data = format_pie_chart_data(data, 'label', 'count')
    elif chart_type == 'doughnut':
        from .utils import format_doughnut_chart_data
        chart_data = format_doughnut_chart_data(data, 'label', 'count')
    elif chart_type == 'bar':
        chart_data = format_bar_chart_data(data, 'label', 'count', 'Equipment Connectivity')
    
    metadata = {
        'total_equipment': sum(item['count'] for item in data)
    }
    
    return format_analytics_response(data, chart_data, metadata), 200


@bp_analytics_equipment.route("/summary", methods=["GET"])
@jwt_required()
@require_access("guest")
def get_equipment_summary():
    
    # Total equipment
    total_query = "SELECT COUNT(*) as total FROM equipment_sets"
    total_result = database.fetch_one(total_query)
    
    # Functional equipment
    functional_query = "SELECT COUNT(*) as functional FROM equipment_sets WHERE functionability = 'functional'"
    functional_result = database.fetch_one(functional_query)
    
    # Equipment with issues
    issues_query = "SELECT COUNT(*) as with_issues FROM equipment_sets WHERE issue_description IS NOT NULL AND issue_description != ''"
    issues_result = database.fetch_one(issues_query)
    
    # Equipment by status
    status_query = """
        SELECT 
            status as label,
            COUNT(*) as count
        FROM equipment_sets
        GROUP BY status
        ORDER BY count DESC
    """
    status_result = database.fetch_all(status_query)
    
    # Check if all queries succeeded
    if not all([total_result['success'], functional_result['success'], 
                issues_result['success'], status_result['success']]):
        return common_database_error_response({'success': False, 'msg': 'Failed to fetch summary data'})
    
    # Compile summary data
    summary_data = {
        'total_equipment': total_result['data']['total'] if total_result['data'] else 0,
        'functional_equipment': functional_result['data']['functional'] if functional_result['data'] else 0,
        'equipment_with_issues': issues_result['data']['with_issues'] if issues_result['data'] else 0,
        'status_breakdown': status_result['data']
    }
    
    # Create chart for status breakdown
    chart_data = format_pie_chart_data(status_result['data'], 'label', 'count')
    
    return format_analytics_response(summary_data, chart_data), 200


@bp_analytics_equipment.route("/dashboard-metrics", methods=["GET"])
@jwt_required()
@require_access("guest")
def get_dashboard_metrics():
    
    # Operational equipment (functional and active)
    operational_query = """
        SELECT COUNT(*) as count 
        FROM equipment_sets 
        WHERE functionability = 'functional' AND status = 'active'
    """
    
    # Missing equipment (equipment sets without complete component information)
    missing_query = """
        SELECT COUNT(DISTINCT es.id) as count
        FROM equipment_sets es
        LEFT JOIN equipment_set_components esc ON es.id = esc.equipment_set_id
        WHERE esc.equipment_set_id IS NULL 
           OR (esc.system_unit_name IS NULL OR esc.system_unit_name = '')
           OR (esc.system_unit_serial_number IS NULL OR esc.system_unit_serial_number = '')
           OR (esc.monitor_name IS NULL OR esc.monitor_name = '')
           OR (esc.monitor_serial_number IS NULL OR esc.monitor_serial_number = '')
    """
    
    # Equipment sets under maintenance
    maintenance_query = """
        SELECT COUNT(*) as count 
        FROM equipment_sets 
        WHERE status = 'maintenance' OR status = 'under_maintenance'
    """
    
    # Equipment sets with connectivity or functionality issues
    issues_query = """
        SELECT COUNT(*) as count 
        FROM equipment_sets 
        WHERE (internet_connectivity = 0 OR functionability != 'functional')
           OR (issue_description IS NOT NULL AND issue_description != '')
    """
    
    # Execute all queries
    operational_result = database.fetch_one(operational_query)
    missing_result = database.fetch_one(missing_query)
    maintenance_result = database.fetch_one(maintenance_query)
    issues_result = database.fetch_one(issues_query)
    
    # Check if all queries succeeded
    if not all([operational_result['success'], missing_result['success'], 
                maintenance_result['success'], issues_result['success']]):
        return common_database_error_response({'success': False, 'msg': 'Failed to fetch dashboard metrics'})
    
    # Compile dashboard metrics
    dashboard_metrics = {
        'operational_equipment': operational_result['data']['count'] if operational_result['data'] else 0,
        'missing_equipment': missing_result['data']['count'] if missing_result['data'] else 0,
        'equipment_under_maintenance': maintenance_result['data']['count'] if maintenance_result['data'] else 0,
        'equipment_with_issues': issues_result['data']['count'] if issues_result['data'] else 0
    }
    
    # Create chart data for visualization
    chart_data_list = [
        {'label': 'Operational', 'count': dashboard_metrics['operational_equipment']},
        {'label': 'Missing Info', 'count': dashboard_metrics['missing_equipment']},
        {'label': 'Under Maintenance', 'count': dashboard_metrics['equipment_under_maintenance']},
        {'label': 'With Issues', 'count': dashboard_metrics['equipment_with_issues']}
    ]
    
    chart_data = format_pie_chart_data(chart_data_list, 'label', 'count')
    
    # Calculate total and percentages
    total_equipment = sum(dashboard_metrics.values())
    metadata = {
        'total_equipment_analyzed': total_equipment,
        'operational_percentage': round((dashboard_metrics['operational_equipment'] / total_equipment * 100), 2) if total_equipment > 0 else 0,
        'issues_percentage': round((dashboard_metrics['equipment_with_issues'] / total_equipment * 100), 2) if total_equipment > 0 else 0
    }
    
    return format_analytics_response(dashboard_metrics, chart_data, metadata), 200
