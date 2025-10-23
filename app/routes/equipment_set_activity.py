from flask import Blueprint, jsonify, request
from ..services.jwt import require_access
from ..services import database
from flask_jwt_extended import jwt_required
from ..config import config
from ..services.validation import check_order_parameter, common_success_response, common_database_error_response

bp_equipment_set_activity = Blueprint("equipment_set_activity", __name__)

@bp_equipment_set_activity.route("/", methods=["GET"])
@jwt_required()
@require_access("guest")
def get():
    base_query = """
        select
            eq_act.id,
            eq_act.performed_by_account_id as account_id,
            a.first_name as account_first_name,
            a.middle_name as account_middle_name,
            a.last_name as account_last_name,
            eq_act.equipment_set_id,
            eq_act.action,
            eq_act.value,
            eq_act.created_at,
        from equipment_set_activity as eq_act
        inner join accounts as a on eq_act.performed_by_account_id = a.id
    """

    # CONDITIONALS
    conditional_query = []
    conditional_params = []


    # filter by id
    if 'id' in request.args and request.args.get('id'):
        conditional_query.append("eq_act.id = %s")
        conditional_params.append()


    # filter by account id
    if 'account_id' in request.args and request.args.get('account_id'):
        conditional_query.append("eq_act.account_id = %s")
        conditional_params.append(request.args.get('account_id'))
    
    # filter by equipment set id
    if 'equipment_set_id' in request.args and request.args.get('equipment_set_id'):
        conditional_query.append("eq_act.equipment_set_id = %s")
        conditional_params.append(request.args.get('equipment_set_id'))


    # filter by action
    if 'component_type' in request.args and request.args.get('component_type'):
        conditional_query.append("eq_act.component_type = %s")
        conditional_params.append(request.args.get('component_type'))

    # filter by action
    if 'action' in request.args and request.args.get('action'):
        conditional_query.append("eq_act.action = %s")
        conditional_params.append(request.args.get('action'))

    # build conditional query
    if conditional_query:
        base_query += " WHERE " + " AND ".join(conditional_query)
        

    # ORDERING OF RECORDS BY RECENTLY CREATED
    if 'order' in request.args:
        order = check_order_parameter(request.args.get('order'))
        base_query += f" ORDER BY eq_act.created_at {order}"
    
    # closing statements
    base_query += ";"

    # execute query
    account_logs_fetch = database.fetch_all(base_query, tuple(conditional_params))

    # query fails
    if not account_logs_fetch['success']:
        return common_database_error_response(account_logs_fetch)

    # success
    return common_success_response(account_logs_fetch['data'])



# HELPER FUNCTIONS ONLY
def log_equipment_set_activity(equipment_set_id, account_id, target_component = 'other', action = 'updated', description='') -> bool:
    base_query = """
        insert into equipment_set_activity
        (
            equipment_set_activity.equipment_set_id,
            equipment_set_activity.account_id,
            equipment_set_activity.target_component,
            equipment_set_activity.action,
            equipment_set_activity.description
        )
        values (%s, %s, %s, %s, %s);
    """
    base_params = (
        equipment_set_id, 
        account_id, 
        target_component, 
        action, 
        description
    )
    
    database.execute_single(base_query, base_params)