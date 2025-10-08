"""
Analytics routes for activity and log-related data.
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

bp_analytics_activity = Blueprint("analytics_activity", __name__)


@bp_analytics_activity.route("/user-actions", methods=["GET"])
@jwt_required()
@require_access("admin")
def get_user_actions():
    # get query parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    user_id = request.args.get('user_id')
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
    
    # user filter
    if user_id:
        query += " AND al.account_id = %s"
        params.append(user_id)
    
    query += " GROUP BY al.action ORDER BY count DESC"
    
    # execute query
    result = database.fetch_all(query, tuple(params))
    
    if not result['success']:
        return common_database_error_response(result)
    
    data = result['data']
    
    # format chart data
    chart_data = None
    if chart_type == 'bar':
        chart_data = format_bar_chart_data(data, 'label', 'count', 'User Actions')
    elif chart_type == 'pie':
        chart_data = format_pie_chart_data(data, 'label', 'count')
    
    metadata = {
        'total_actions': sum(item['count'] for item in data),
        'user_filter': user_id,
        'date_range': {
            'start_date': start_date,
            'end_date': end_date
        }
    }
    
    return format_analytics_response(data, chart_data, metadata), 200


@bp_analytics_activity.route("/activity-trends", methods=["GET"])
@jwt_required()
@require_access("admin")
def get_activity_trends():
    
    # get query parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    period = request.args.get('period', 'daily')  # aily, weekly, monthly
    action_filter = request.args.get('action')
    
    # query for activity trends
    query = """
        SELECT 
            DATE(al.created_at) as date,
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
    
    query += " GROUP BY DATE(al.created_at) ORDER BY date"
    
    # execute
    result = database.fetch_all(query, tuple(params))
    
    if not result['success']:
        return common_database_error_response(result)
    
    # process data for time series
    raw_data = result['data']
    time_series_data = get_time_series_data(raw_data, 'date', 'count', period)
    
    # format for line chart
    chart_data = format_line_chart_data(time_series_data, 'date', 'value', 'Activity Trends')
    
    metadata = {
        'period': period,
        'action_filter': action_filter,
        'total_records': len(time_series_data),
        'date_range': {
            'start_date': start_date,
            'end_date': end_date
        }
    }
    
    return format_analytics_response(time_series_data, chart_data, metadata), 200


@bp_analytics_activity.route("/top-users", methods=["GET"])
@jwt_required()
@require_access("admin")
def get_top_active_users():
    
    # parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    limit = int(request.args.get('limit', 10))
    chart_type = request.args.get('chart_type', 'bar')
    
    # base query
    query = """
        SELECT 
            CONCAT(a.first_name, ' ', a.last_name) as label,
            a.username,
            COUNT(al.id) as count
        FROM account_logs al
        INNER JOIN accounts a ON al.account_id = a.id
        WHERE 1=1
    """
    
    params = []
    
    # date range filter
    if start_date or end_date:
        date_condition, date_params = get_date_range_filter(start_date, end_date)
        if date_condition:
            query += f" AND {date_condition.replace('created_at', 'al.created_at')}"
            params.extend(date_params)
    
    query += f" GROUP BY a.id, a.first_name, a.last_name, a.username ORDER BY count DESC LIMIT {limit}"
    
    # execute
    result = database.fetch_all(query, tuple(params))
    
    if not result['success']:
        return common_database_error_response(result)
    
    data = result['data']
    
    # format chart data
    chart_data = None
    if chart_type == 'bar':
        chart_data = format_bar_chart_data(data, 'label', 'count', 'Most Active Users')
    elif chart_type == 'pie':
        chart_data = format_pie_chart_data(data, 'label', 'count')
    
    metadata = {
        'total_users': len(data),
        'limit': limit,
        'date_range': {
            'start_date': start_date,
            'end_date': end_date
        }
    }
    
    return format_analytics_response(data, chart_data, metadata), 200


@bp_analytics_activity.route("/hourly-distribution", methods=["GET"])
@jwt_required()
@require_access("admin")
def get_hourly_activity_distribution():
    # get query parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # query for hourly activity distribution
    query = """
        SELECT 
            HOUR(al.created_at) as hour,
            COUNT(*) as count
        FROM account_logs al
        WHERE 1=1
    """
    
    params = []
    
    if start_date or end_date:
        date_condition, date_params = get_date_range_filter(start_date, end_date)
        if date_condition:
            query += f" AND {date_condition.replace('created_at', 'al.created_at')}"
            params.extend(date_params)
    
    query += " GROUP BY HOUR(al.created_at) ORDER BY hour"
    
    result = database.fetch_all(query, tuple(params))
    
    if not result['success']:
        return common_database_error_response(result)
    
    data = result['data']
    
    formatted_data = []
    for item in data:
        hour = item['hour']
        hour_label = f"{hour:02d}:00"
        formatted_data.append({
            'label': hour_label,
            'count': item['count']
        })
    
    # format as bar chart
    chart_data = format_bar_chart_data(formatted_data, 'label', 'count', 'Activity by Hour')
    
    metadata = {
        'total_activities': sum(item['count'] for item in formatted_data),
        'date_range': {
            'start_date': start_date,
            'end_date': end_date
        }
    }
    
    return format_analytics_response(formatted_data, chart_data, metadata), 200


@bp_analytics_activity.route("/equipment-history", methods=["GET"])
@jwt_required()
@require_access("guest")
def get_equipment_history_analytics():
    
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    equipment_id = request.args.get('equipment_id')
    chart_type = request.args.get('chart_type', 'line')
    
    query = """
        SELECT 
            DATE(eh.created_at) as date,
            COUNT(*) as count
        FROM equipment_set_history eh
        WHERE 1=1
    """
    
    params = []
    
    if start_date or end_date:
        date_condition, date_params = get_date_range_filter(start_date, end_date)
        if date_condition:
            query += f" AND {date_condition.replace('created_at', 'eh.created_at')}"
            params.extend(date_params)
    
    if equipment_id:
        query += " AND eh.equipment_set_id = %s"
        params.append(equipment_id)
    
    query += " GROUP BY DATE(eh.created_at) ORDER BY date"
    
    result = database.fetch_all(query, tuple(params))
    
    if not result['success']:
        return common_database_error_response(result)
    
    data = result['data']
    
    chart_data = None
    if chart_type == 'line':
        chart_data = format_line_chart_data(data, 'date', 'count', 'Equipment Changes')
    elif chart_type == 'bar':
        chart_data = format_bar_chart_data(data, 'date', 'count', 'Equipment Changes')
    
    metadata = {
        'total_changes': sum(item['count'] for item in data),
        'equipment_filter': equipment_id,
        'date_range': {
            'start_date': start_date,
            'end_date': end_date
        }
    }
    
    return format_analytics_response(data, chart_data, metadata), 200


@bp_analytics_activity.route("/summary", methods=["GET"])
@jwt_required()
@require_access("admin")
def get_activity_summary():
    
    today_query = """
        SELECT COUNT(*) as today_count
        FROM account_logs 
        WHERE DATE(created_at) = CURDATE()
    """
    today_result = database.fetch_one(today_query)
    
    week_query = """
        SELECT COUNT(*) as week_count
        FROM account_logs 
        WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    """
    week_result = database.fetch_one(week_query)
    
    action_query = """
        SELECT action, COUNT(*) as count
        FROM account_logs 
        GROUP BY action 
        ORDER BY count DESC 
        LIMIT 1
    """
    action_result = database.fetch_one(action_query)
    
    user_query = """
        SELECT 
            CONCAT(a.first_name, ' ', a.last_name) as user_name,
            COUNT(al.id) as activity_count
        FROM account_logs al
        INNER JOIN accounts a ON al.account_id = a.id
        WHERE al.created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        GROUP BY a.id, a.first_name, a.last_name
        ORDER BY activity_count DESC
        LIMIT 1
    """
    user_result = database.fetch_one(user_query)
    
    if not all([today_result['success'], week_result['success'], 
                action_result['success'], user_result['success']]):
        return common_database_error_response({'success': False, 'msg': 'Failed to fetch summary data'})
    
    summary_data = {
        'activities_today': today_result['data']['today_count'] if today_result['data'] else 0,
        'activities_this_week': week_result['data']['week_count'] if week_result['data'] else 0,
        'most_common_action': action_result['data']['action'] if action_result['data'] else 'N/A',
        'most_active_user': user_result['data']['user_name'] if user_result['data'] else 'N/A',
        'most_active_user_count': user_result['data']['activity_count'] if user_result['data'] else 0
    }
    
    return format_analytics_response(summary_data), 200
