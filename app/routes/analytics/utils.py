"""
Analytics utilities for standardized chart data formats and common analytics functions.
"""
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
import calendar


def format_pie_chart_data(data: List[Dict[str, Any]], label_key: str, value_key: str) -> Dict[str, Any]:
    return {
        "type": "pie",
        "data": {
            "labels": [item[label_key] for item in data],
            "datasets": [{
                "data": [item[value_key] for item in data],
                "backgroundColor": [
                    "#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0", 
                    "#9966FF", "#FF9F40", "#FF6384", "#C9CBCF"
                ][:len(data)]
            }]
        },
        "options": {
            "responsive": True,
            "plugins": {
                "legend": {
                    "position": "right"
                }
            }
        }
    }


def format_bar_chart_data(data: List[Dict[str, Any]], label_key: str, value_key: str, title: str = "Bar Chart") -> Dict[str, Any]:
    return {
        "type": "bar",
        "data": {
            "labels": [item[label_key] for item in data],
            "datasets": [{
                "label": title,
                "data": [item[value_key] for item in data],
                "backgroundColor": "#36A2EB",
                "borderColor": "#36A2EB",
                "borderWidth": 1
            }]
        },
        "options": {
            "responsive": True,
            "plugins": {
                "legend": {
                    "display": False
                }
            },
            "scales": {
                "y": {
                    "beginAtZero": True
                }
            }
        }
    }


def format_line_chart_data(data: List[Dict[str, Any]], label_key: str, value_key: str, title: str = "Line Chart") -> Dict[str, Any]:
    return {
        "type": "line",
        "data": {
            "labels": [item[label_key] for item in data],
            "datasets": [{
                "label": title,
                "data": [item[value_key] for item in data],
                "borderColor": "#36A2EB",
                "backgroundColor": "rgba(54, 162, 235, 0.1)",
                "fill": True,
                "tension": 0.4
            }]
        },
        "options": {
            "responsive": True,
            "plugins": {
                "legend": {
                    "display": True
                }
            },
            "scales": {
                "y": {
                    "beginAtZero": True
                }
            }
        }
    }


def format_doughnut_chart_data(data: List[Dict[str, Any]], label_key: str, value_key: str) -> Dict[str, Any]:
    return {
        "type": "doughnut",
        "data": {
            "labels": [item[label_key] for item in data],
            "datasets": [{
                "data": [item[value_key] for item in data],
                "backgroundColor": [
                    "#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0", 
                    "#9966FF", "#FF9F40", "#FF6384", "#C9CBCF"
                ][:len(data)]
            }]
        },
        "options": {
            "responsive": True,
            "plugins": {
                "legend": {
                    "position": "right"
                }
            }
        }
    }


def get_date_range_filter(start_date: Optional[str] = None, end_date: Optional[str] = None) -> tuple:
    conditions = []
    params = []
    
    if start_date:
        conditions.append("DATE(created_at) >= %s")
        params.append(start_date)
    
    if end_date:
        conditions.append("DATE(created_at) <= %s")
        params.append(end_date)
    
    return (" AND ".join(conditions), params)


def get_time_series_data(data: List[Dict[str, Any]], date_key: str, value_key: str, period: str = "daily") -> List[Dict[str, Any]]:
    grouped_data = {}
    
    for item in data:
        date_val = item[date_key]
        if isinstance(date_val, str):
            date_val = datetime.fromisoformat(date_val.replace('Z', '+00:00'))
        
        if period == "daily":
            key = date_val.strftime("%Y-%m-%d")
        elif period == "weekly":
            # Get Monday of the week
            monday = date_val - timedelta(days=date_val.weekday())
            key = monday.strftime("%Y-%m-%d")
        elif period == "monthly":
            key = date_val.strftime("%Y-%m")
        else:
            key = date_val.strftime("%Y-%m-%d")
        
        if key not in grouped_data:
            grouped_data[key] = 0
        grouped_data[key] += item[value_key]
    
    # Convert to list format
    result = []
    for date_key, value in sorted(grouped_data.items()):
        result.append({
            "date": date_key,
            "value": value
        })
    
    return result


def calculate_percentage_change(current: int, previous: int) -> float:
    if previous == 0:
        return 100.0 if current > 0 else 0.0
    
    return ((current - previous) / previous) * 100


def format_analytics_response(data: Any, chart_data: Optional[Dict[str, Any]] = None, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    response = {
        "success": True,
        "data": data
    }
    
    if chart_data:
        response["chart"] = chart_data
    
    if metadata:
        response["metadata"] = metadata
    
    return response
