from flask import Blueprint, jsonify, request
from services.jwt import require_access
import services.database as database
from flask_jwt_extended import jwt_required
from config import config

bp_equipment_set_history = Blueprint("equipment_set_history", __name__)

@bp_equipment_set_history.route("/", methods=["GET"])
@jwt_required()
@require_access("guest")
def get():
    # setup base query
    base_query = """
        select
            eq_his.id,
            eq_his.equipment_set_id,
            eq_his.account_id,
            a.username as account_username,
            a.first_name as account_first_name,
            a.middle_name as account_middle_name,
            a.last_name as account_last_name,
            eq_his.component_type,
            eq_his.action,
            eq_his.description,
            eq_his.created_at

        from equipment_set_history as eq_his
        inner join accounts as a on eq_his.account_id = a.id
    """

    # CONDITIONALS
    conditional_query = []
    conditional_params = []


    # filter by id
    if 'id' in request.args:
        conditional_query.append("eq_his.id = %s")
        conditional_params.append(request.args.get('id'))


    # filter by account id
    if 'account_id' in request.args:
        conditional_query.append("eq_his.account_id = %s")
        conditional_params.append(request.args.get('account_id'))
    
    # filter by equipment set id
    if 'account_id' in request.args:
        conditional_query.append("eq_his.equipment_set_id = %s")
        conditional_params.append(request.args.get('equipment_set_id'))


    # filter by action
    if 'component_type' in request.args:
        conditional_query.append("eq_his.component_type = %s")
        conditional_params.append(request.args.get('component_type'))

    # filter by action
    if 'action' in request.args:
        conditional_query.append("eq_his.action = %s")
        conditional_params.append(request.args.get('action'))

    # build conditional query
    if conditional_query:
        base_query += " WHERE " + " AND ".join(conditional_query)
        

    # ORDERING OF RECORDS BY RECENTLY CREATED
    if 'order' in request.args:
        order = "DESC" if request.args.get('order') == "latest" else "ASC"
        base_query += f" ORDER BY eq_his.created_at {order}"
    
    # closing statements
    base_query += ";"

    # execute query
    account_logs_fetch = database.fetch_all(base_query, tuple(conditional_params))

    # query fails
    if not account_logs_fetch['success']:
        result = jsonify({
            "msg": account_logs_fetch['msg']
        })
        return result, 400

    # success
    return jsonify({
        "data": account_logs_fetch['data']
    }), 200



# HELPER FUNCTIONS ONLY
def log_equipment_set_activity(equipment_set_id, account_id, target_component = 'other', action = 'updated', description='') -> bool:
    base_query = """
        insert into equipment_set_history
        (
            equipment_set_history.equipment_set_id,
            equipment_set_history.account_id,
            equipment_set_history.target_component,
            equipment_set_history.action,
            equipment_set_history.description
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