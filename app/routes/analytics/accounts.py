# Analytics routes for account-related data and visualizations.
from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from ...services.jwt import require_access
from ...services import database
from ...services.validation import common_success_response, common_database_error_response
from .utils import (
    format_pie_chart_data, format_bar_chart_data, format_line_chart_data,
    get_date_range_filter, get_time_series_data, format_analytics_response
)

bp_analytics_accounts = Blueprint("analytics_accounts", __name__)

# get account counts with filters and breakdown
@bp_analytics_accounts.route("/counts", methods=["GET"])
@jwt_required()
@require_access("admin")
def get_account_counts():    
    # parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    group_by = request.args.get('group_by', 'status')  # status, role, created_date
    chart_type = request.args.get('chart_type', 'pie')
    
    # base query
    if group_by == 'status':
        query = """
            SELECT 
                a.status as label,
                COUNT(*) as count
            FROM accounts a
            WHERE 1=1
        """
    elif group_by == 'role':
        query = """
            SELECT 
                ar.name as label,
                COUNT(*) as count
            FROM accounts a
            INNER JOIN account_roles ar ON a.role_id = ar.id
            WHERE 1=1
        """
    elif group_by == 'created_date':
        query = """
            SELECT 
                DATE(a.created_at) as label,
                COUNT(*) as count
            FROM accounts a
            WHERE 1=1
        """
    else:
        query = """
            SELECT 
                a.status as label,
                COUNT(*) as count
            FROM accounts a
            WHERE 1=1
        """
    
    # date range filter
    params = []
    if start_date or end_date:
        date_condition, date_params = get_date_range_filter(start_date, end_date)
        if date_condition:
            query += f" AND {date_condition}"
            params.extend(date_params)
    
    query += " GROUP BY label ORDER BY count DESC"
    
    # execute query
    result = database.fetch_all(query, tuple(params))
    
    if not result['success']:
        return common_database_error_response(result)
    
    data = result['data']
    
    # format chart data based on requested type
    chart_data = None
    if chart_type == 'pie':
        chart_data = format_pie_chart_data(data, 'label', 'count')
    elif chart_type == 'bar':
        chart_data = format_bar_chart_data(data, 'label', 'count', f'Accounts by {group_by.title()}')
    elif chart_type == 'doughnut':
        from .utils import format_doughnut_chart_data
        chart_data = format_doughnut_chart_data(data, 'label', 'count')
    
    # foramt return data
    total_accounts = sum(item['count'] for item in data)
    metadata = {
        'total_accounts': total_accounts,
        'group_by': group_by,
        'date_range': {
            'start_date': start_date,
            'end_date': end_date
        }
    }
    
    return format_analytics_response(data, chart_data, metadata), 200

# get account creation trends over time
@bp_analytics_accounts.route("/trends", methods=["GET"])
@jwt_required()
@require_access("admin")
def get_account_trends():
    
    # parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    period = request.args.get('period', 'daily')  # daily, weekly, monthly
    
    # base query
    query = """
        SELECT 
            DATE(created_at) as date,
            COUNT(*) as count
        FROM accounts
        WHERE 1=1
    """
    
    params = []
    if start_date or end_date:
        date_condition, date_params = get_date_range_filter(start_date, end_date)
        if date_condition:
            query += f" AND {date_condition}"
            params.extend(date_params)
    
    query += " GROUP BY DATE(created_at) ORDER BY date"
    
    # execute query
    result = database.fetch_all(query, tuple(params))
    
    if not result['success']:
        return common_database_error_response(result)
    
    # process data for time series
    raw_data = result['data']
    time_series_data = get_time_series_data(raw_data, 'date', 'count', period)
    
    # format for line chart
    chart_data = format_line_chart_data(time_series_data, 'date', 'value', 'Account Registrations')
    
    metadata = {
        'period': period,
        'total_records': len(time_series_data),
        'date_range': {
            'start_date': start_date,
            'end_date': end_date
        }
    }
    
    return format_analytics_response(time_series_data, chart_data, metadata), 200

# get comprehensive account analytics summary
@bp_analytics_accounts.route("/summary", methods=["GET"])
@jwt_required()
@require_access("admin")
def get_account_summary():    
    # total accounts
    total_query = "SELECT COUNT(*) as total FROM accounts"
    total_result = database.fetch_one(total_query)
    
    # active accounts
    active_query = "SELECT COUNT(*) as active FROM accounts WHERE status = 'active'"
    active_result = database.fetch_one(active_query)
    
    # accounts by role
    role_query = """
        SELECT 
            ar.name as role_name,
            COUNT(*) as count
        FROM accounts a
        INNER JOIN account_roles ar ON a.role_id = ar.id
        GROUP BY ar.name
        ORDER BY count DESC
    """
    role_result = database.fetch_all(role_query)
    
    # recent registrations (last 30 days)
    recent_query = """
        SELECT COUNT(*) as recent
        FROM accounts 
        WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
    """
    recent_result = database.fetch_one(recent_query)
    
    # check if all queries succeeded
    if not all([total_result['success'], active_result['success'], 
                role_result['success'], recent_result['success']]):
        return common_database_error_response({'success': False, 'msg': 'Failed to fetch summary data'})
    
    # format summary data
    summary_data = {
        'total_accounts': total_result['data']['total'] if total_result['data'] else 0,
        'active_accounts': active_result['data']['active'] if active_result['data'] else 0,
        'recent_registrations': recent_result['data']['recent'] if recent_result['data'] else 0,
        'roles_breakdown': role_result['data']
    }
    
    # create chart for roles breakdown
    chart_data = format_pie_chart_data(role_result['data'], 'role_name', 'count')
    
    return format_analytics_response(summary_data, chart_data), 200


# get account activity analytics from account logs
@bp_analytics_accounts.route("/activity", methods=["GET"])
@jwt_required()
@require_access("admin")
def get_account_activity():
    # parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    action_filter = request.args.get('action')
    chart_type = request.args.get('chart_type', 'bar')
    
    # base query
    query = """
        SELECT 
            al.action as label,
            COUNT(*) as count
        FROM account_logs al
        WHERE 1=1
    """
    
    params = []
    
    # date range filter
    if start_date or end_date:
        date_condition, date_params = get_date_range_filter(start_date, end_date)
        if date_condition:
            query += f" AND {date_condition.replace('created_at', 'al.created_at')}"
            params.extend(date_params)
    
    # action filter
    if action_filter:
        query += " AND al.action = %s"
        params.append(action_filter)
    
    query += " GROUP BY al.action ORDER BY count DESC"
    
    # execute query
    result = database.fetch_all(query, tuple(params))
    
    if not result['success']:
        return common_database_error_response(result)
    
    data = result['data']
    
    # format chart data
    chart_data = None
    if chart_type == 'bar':
        chart_data = format_bar_chart_data(data, 'label', 'count', 'Account Activity')
    elif chart_type == 'pie':
        chart_data = format_pie_chart_data(data, 'label', 'count')
    
    # format metadata
    total_activities = sum(item['count'] for item in data)
    metadata = {
        'total_activities': total_activities,
        'action_filter': action_filter,
        'date_range': {
            'start_date': start_date,
            'end_date': end_date
        }
    }
    
    return format_analytics_response(data, chart_data, metadata), 200
