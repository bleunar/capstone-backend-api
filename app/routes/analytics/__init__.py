# Analytics module for providing analytical data and visualizations.
from .accounts import bp_analytics_accounts
from .equipment import bp_analytics_equipment
from .activity import bp_analytics_activity
from .overview import bp_analytics_overview

__all__ = [
    'bp_analytics_accounts',
    'bp_analytics_equipment', 
    'bp_analytics_activity',
    'bp_analytics_overview'
]
