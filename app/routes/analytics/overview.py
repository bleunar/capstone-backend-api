"""
Analytics routes for system overview and dashboard data.
"""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from ...services.jwt import require_access
from ...services import database
from ...services.validation import common_database_error_response
from .utils import (
    format_pie_chart_data, format_bar_chart_data, format_line_chart_data,
    get_date_range_filter, format_analytics_response, calculate_percentage_change
)

bp_analytics_overview = Blueprint("analytics_overview", __name__)


@bp_analytics_overview.route("/dashboard", methods=["GET"])
@jwt_required()
@require_access("guest")
def get_dashboard_overview():
    
    # Key metrics queries
    queries = {
        'total_accounts': "SELECT COUNT(*) as count FROM accounts",
        'active_accounts': "SELECT COUNT(*) as count FROM accounts WHERE status = 'active'",
        'total_equipment': "SELECT COUNT(*) as count FROM equipment_sets",
        'functional_equipment': "SELECT COUNT(*) as count FROM equipment_sets WHERE functionability = 'functional'",
        'total_locations': "SELECT COUNT(*) as count FROM locations",
        'recent_activities': "SELECT COUNT(*) as count FROM account_logs WHERE created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)"
    }
    
    # Dashboard-specific equipment metrics
    dashboard_equipment_queries = {
        'operational_equipment': """
            SELECT COUNT(*) as count 
            FROM equipment_sets 
            WHERE functionability = 'functional' AND status = 'active'
        """,
        'missing_equipment': """
            SELECT COUNT(DISTINCT es.id) as count
            FROM equipment_sets es
            LEFT JOIN equipment_set_components esc ON es.id = esc.equipment_set_id
            WHERE esc.equipment_set_id IS NULL 
               OR (esc.system_unit_name IS NULL OR esc.system_unit_name = '')
               OR (esc.system_unit_serial_number IS NULL OR esc.system_unit_serial_number = '')
               OR (esc.monitor_name IS NULL OR esc.monitor_name = '')
               OR (esc.monitor_serial_number IS NULL OR esc.monitor_serial_number = '')
        """,
        'equipment_under_maintenance': """
            SELECT COUNT(*) as count 
            FROM equipment_sets 
            WHERE status = 'maintenance' OR status = 'under_maintenance'
        """,
        'equipment_with_issues': """
            SELECT COUNT(*) as count 
            FROM equipment_sets 
            WHERE (internet_connectivity = 0 OR functionability != 'functional')
               OR (issue_description IS NOT NULL AND issue_description != '')
        """
    }
    
    # Execute all queries
    results = {}
    for key, query in queries.items():
        result = database.fetch_one(query)
        if not result['success']:
            return common_database_error_response(result)
        results[key] = result['data']['count'] if result['data'] else 0
    
    # Execute dashboard equipment queries
    dashboard_results = {}
    for key, query in dashboard_equipment_queries.items():
        result = database.fetch_one(query)
        if not result['success']:
            return common_database_error_response(result)
        dashboard_results[key] = result['data']['count'] if result['data'] else 0
    
    # Calculate equipment health percentage
    equipment_health = 0
    if results['total_equipment'] > 0:
        equipment_health = (results['functional_equipment'] / results['total_equipment']) * 100
    
    # Calculate account activation rate
    account_activation = 0
    if results['total_accounts'] > 0:
        account_activation = (results['active_accounts'] / results['total_accounts']) * 100
    
    # Compile dashboard data
    dashboard_data = {
        'key_metrics': {
            'total_accounts': results['total_accounts'],
            'active_accounts': results['active_accounts'],
            'total_equipment': results['total_equipment'],
            'functional_equipment': results['functional_equipment'],
            'total_locations': results['total_locations'],
            'recent_activities': results['recent_activities']
        },
        'equipment_dashboard_metrics': {
            'operational_equipment': dashboard_results['operational_equipment'],
            'missing_equipment': dashboard_results['missing_equipment'],
            'equipment_under_maintenance': dashboard_results['equipment_under_maintenance'],
            'equipment_with_issues': dashboard_results['equipment_with_issues']
        },
        'health_indicators': {
            'equipment_health_percentage': round(equipment_health, 2),
            'account_activation_percentage': round(account_activation, 2),
            'operational_percentage': round((dashboard_results['operational_equipment'] / results['total_equipment'] * 100), 2) if results['total_equipment'] > 0 else 0,
            'issues_percentage': round((dashboard_results['equipment_with_issues'] / results['total_equipment'] * 100), 2) if results['total_equipment'] > 0 else 0
        }
    }
    
    return format_analytics_response(dashboard_data), 200


@bp_analytics_overview.route("/system-health", methods=["GET"])
@jwt_required()
@require_access("admin")
def get_system_health():
    
    # Equipment health breakdown
    equipment_health_query = """
        SELECT 
            functionability as status,
            COUNT(*) as count
        FROM equipment_sets
        GROUP BY functionability
    """
    equipment_result = database.fetch_all(equipment_health_query)
    
    # Account status breakdown
    account_status_query = """
        SELECT 
            status,
            COUNT(*) as count
        FROM accounts
        GROUP BY status
    """
    account_result = database.fetch_all(account_status_query)
    
    # Equipment connectivity status
    connectivity_query = """
        SELECT 
            CASE 
                WHEN internet_connectivity = 1 THEN 'Connected'
                ELSE 'Disconnected'
            END as status,
            COUNT(*) as count
        FROM equipment_sets
        GROUP BY internet_connectivity
    """
    connectivity_result = database.fetch_all(connectivity_query)
    
    # Check if all queries succeeded
    if not all([equipment_result['success'], account_result['success'], connectivity_result['success']]):
        return common_database_error_response({'success': False, 'msg': 'Failed to fetch health data'})
    
    # Create charts for each health indicator
    equipment_chart = format_pie_chart_data(equipment_result['data'], 'status', 'count')
    account_chart = format_pie_chart_data(account_result['data'], 'status', 'count')
    connectivity_chart = format_pie_chart_data(connectivity_result['data'], 'status', 'count')
    
    health_data = {
        'equipment_health': equipment_result['data'],
        'account_status': account_result['data'],
        'connectivity_status': connectivity_result['data']
    }
    
    charts = {
        'equipment_health_chart': equipment_chart,
        'account_status_chart': account_chart,
        'connectivity_chart': connectivity_chart
    }
    
    return format_analytics_response(health_data, charts), 200


@bp_analytics_overview.route("/growth-metrics", methods=["GET"])
@jwt_required()
@require_access("admin")
def get_growth_metrics():
    
    # Get query parameters
    period = request.args.get('period', 'monthly')  # daily, weekly, monthly
    
    # Account growth query
    if period == 'daily':
        account_growth_query = """
            SELECT 
                DATE(created_at) as period,
                COUNT(*) as count
            FROM accounts
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            GROUP BY DATE(created_at)
            ORDER BY period
        """
    elif period == 'weekly':
        account_growth_query = """
            SELECT 
                YEARWEEK(created_at) as period,
                COUNT(*) as count
            FROM accounts
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 12 WEEK)
            GROUP BY YEARWEEK(created_at)
            ORDER BY period
        """
    else:  # monthly
        account_growth_query = """
            SELECT 
                DATE_FORMAT(created_at, '%Y-%m') as period,
                COUNT(*) as count
            FROM accounts
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 12 MONTH)
            GROUP BY DATE_FORMAT(created_at, '%Y-%m')
            ORDER BY period
        """
    
    # Equipment additions query
    if period == 'daily':
        equipment_growth_query = """
            SELECT 
                DATE(created_at) as period,
                COUNT(*) as count
            FROM equipment_sets
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            GROUP BY DATE(created_at)
            ORDER BY period
        """
    elif period == 'weekly':
        equipment_growth_query = """
            SELECT 
                YEARWEEK(created_at) as period,
                COUNT(*) as count
            FROM equipment_sets
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 12 WEEK)
            GROUP BY YEARWEEK(created_at)
            ORDER BY period
        """
    else:  # monthly
        equipment_growth_query = """
            SELECT 
                DATE_FORMAT(created_at, '%Y-%m') as period,
                COUNT(*) as count
            FROM equipment_sets
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 12 MONTH)
            GROUP BY DATE_FORMAT(created_at, '%Y-%m')
            ORDER BY period
        """
    
    # Execute queries
    account_result = database.fetch_all(account_growth_query)
    equipment_result = database.fetch_all(equipment_growth_query)
    
    if not all([account_result['success'], equipment_result['success']]):
        return common_database_error_response({'success': False, 'msg': 'Failed to fetch growth data'})
    
    # Format chart data
    account_chart = format_line_chart_data(account_result['data'], 'period', 'count', 'Account Growth')
    equipment_chart = format_line_chart_data(equipment_result['data'], 'period', 'count', 'Equipment Growth')
    
    growth_data = {
        'account_growth': account_result['data'],
        'equipment_growth': equipment_result['data'],
        'period': period
    }
    
    charts = {
        'account_growth_chart': account_chart,
        'equipment_growth_chart': equipment_chart
    }
    
    return format_analytics_response(growth_data, charts), 200


@bp_analytics_overview.route("/location-overview", methods=["GET"])
@jwt_required()
@require_access("guest")
def get_location_overview():
    # Equipment distribution by location
    location_equipment_query = """
        SELECT 
            l.name as location_name,
            COUNT(eq.id) as equipment_count,
            SUM(CASE WHEN eq.functionability = 'functional' THEN 1 ELSE 0 END) as functional_count,
            SUM(CASE WHEN eq.status = 'active' THEN 1 ELSE 0 END) as active_count
        FROM locations l
        LEFT JOIN equipment_sets eq ON l.id = eq.location_id
        GROUP BY l.id, l.name
        ORDER BY equipment_count DESC
    """
    
    # Execute query
    result = database.fetch_all(location_equipment_query)
    
    if not result['success']:
        return common_database_error_response(result)
    
    data = result['data']
    
    # Create charts
    equipment_distribution_chart = format_bar_chart_data(data, 'location_name', 'equipment_count', 'Equipment by Location')
    
    # Calculate health percentages for each location
    for item in data:
        if item['equipment_count'] > 0:
            item['health_percentage'] = round((item['functional_count'] / item['equipment_count']) * 100, 2)
            item['active_percentage'] = round((item['active_count'] / item['equipment_count']) * 100, 2)
        else:
            item['health_percentage'] = 0
            item['active_percentage'] = 0
    
    metadata = {
        'total_locations': len(data),
        'total_equipment': sum(item['equipment_count'] for item in data)
    }
    
    return format_analytics_response(data, equipment_distribution_chart, metadata), 200


@bp_analytics_overview.route("/recent-trends", methods=["GET"])
@jwt_required()
@require_access("guest")
def get_recent_trends():
    # Recent account registrations (last 7 days vs previous 7 days)
    recent_accounts_query = """
        SELECT 
            SUM(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY) THEN 1 ELSE 0 END) as recent,
            SUM(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 14 DAY) 
                     AND created_at < DATE_SUB(NOW(), INTERVAL 7 DAY) THEN 1 ELSE 0 END) as previous
        FROM accounts
    """
    
    # Recent equipment additions
    recent_equipment_query = """
        SELECT 
            SUM(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY) THEN 1 ELSE 0 END) as recent,
            SUM(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 14 DAY) 
                     AND created_at < DATE_SUB(NOW(), INTERVAL 7 DAY) THEN 1 ELSE 0 END) as previous
        FROM equipment_sets
    """
    
    # Recent activity
    recent_activity_query = """
        SELECT 
            SUM(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY) THEN 1 ELSE 0 END) as recent,
            SUM(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 14 DAY) 
                     AND created_at < DATE_SUB(NOW(), INTERVAL 7 DAY) THEN 1 ELSE 0 END) as previous
        FROM account_logs
    """
    
    # Execute queries
    accounts_result = database.fetch_one(recent_accounts_query)
    equipment_result = database.fetch_one(recent_equipment_query)
    activity_result = database.fetch_one(recent_activity_query)
    
    if not all([accounts_result['success'], equipment_result['success'], activity_result['success']]):
        return common_database_error_response({'success': False, 'msg': 'Failed to fetch trends data'})
    
    # Calculate percentage changes
    accounts_data = accounts_result['data']
    equipment_data = equipment_result['data']
    activity_data = activity_result['data']
    
    trends_data = {
        'account_registrations': {
            'recent': accounts_data['recent'] if accounts_data else 0,
            'previous': accounts_data['previous'] if accounts_data else 0,
            'change_percentage': calculate_percentage_change(
                accounts_data['recent'] if accounts_data else 0,
                accounts_data['previous'] if accounts_data else 0
            )
        },
        'equipment_additions': {
            'recent': equipment_data['recent'] if equipment_data else 0,
            'previous': equipment_data['previous'] if equipment_data else 0,
            'change_percentage': calculate_percentage_change(
                equipment_data['recent'] if equipment_data else 0,
                equipment_data['previous'] if equipment_data else 0
            )
        },
        'user_activity': {
            'recent': activity_data['recent'] if activity_data else 0,
            'previous': activity_data['previous'] if activity_data else 0,
            'change_percentage': calculate_percentage_change(
                activity_data['recent'] if activity_data else 0,
                activity_data['previous'] if activity_data else 0
            )
        }
    }
    
    return format_analytics_response(trends_data), 200
