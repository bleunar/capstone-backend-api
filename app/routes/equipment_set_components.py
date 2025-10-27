from flask import Blueprint, jsonify, request
from ..services.jwt import require_access
from ..services.security import generate_id
from ..services import database
from flask_jwt_extended import jwt_required
from ..config import config
from ..services.validation import check_json_payload
from .equipment_set_activity import log_equipment_set_changes
from flask_jwt_extended import get_jwt_identity
from ..services.validation import check_json_payload, check_required_fields, common_success_response, common_error_response, common_database_error_response


bp_equipment_set_components = Blueprint("equipment_set_components", __name__)


@bp_equipment_set_components.route("/<id>", methods=["GET"])
@jwt_required()
@require_access("guest")
def get(id):

    # setup base query
    base_query = """
        select
            eq_set_comp.equipment_set_id,
            eq_set_comp.system_unit_name,
            eq_set_comp.system_unit_serial_number,
            eq_set_comp.monitor_name,
            eq_set_comp.monitor_serial_number,
            eq_set_comp.keyboard_name,
            eq_set_comp.keyboard_serial_number,
            eq_set_comp.mouse_name,
            eq_set_comp.mouse_serial_number,
            eq_set_comp.avr_name,
            eq_set_comp.avr_serial_number,
            eq_set_comp.headset_name,
            eq_set_comp.headset_serial_number,
            eq_set_comp.updated_at
        from equipment_set_components as eq_set_comp
        where equipment_set_id = %s;
    """

    # execute query
    equipment_set_components_fetch = database.fetch_one(base_query, (id, ))

    # query fails
    if not equipment_set_components_fetch['success']:
        return common_database_error_response(equipment_set_components_fetch)
    
    if equipment_set_components_fetch['data'] is None:
        initialize_equipment_set_components(
            equipment_set_id=id
        )

    # success
    return common_success_response(
        data=equipment_set_components_fetch['data'],
        message="Fetched Equipment Set Component"
    )



@bp_equipment_set_components.route("/<id>", methods=["PUT"])
@jwt_required()
@require_access('default')
def edit(id):
    data, error_response = check_json_payload()
    if error_response:
        return error_response

    # fetch data forms
    sysunit_name = data.get('system_unit_name', '')
    sysunit_serial = data.get('system_unit_serial_number', '')

    mntr_name = data.get('monitor_name', '')
    mntr_serial = data.get('monitor_serial_number', '')

    kbrd_name = data.get('keyboard_name', '')
    kbrd_serial = data.get('keyboard_serial_number', '')

    mouse_name = data.get('mouse_name', '')
    mouse_serial = data.get('mouse_serial_number', '')

    avr_name = data.get('avr_name', '')
    avr_serial = data.get('avr_serial_number', '')

    hset_name = data.get('headset_name', '')
    hset_serial = data.get('headset_serial_number', '')


    # prepare query and parameters
    base_query = """
        update equipment_set_components set
            equipment_set_components.system_unit_name = %s,
            equipment_set_components.system_unit_serial_number = %s,
            equipment_set_components.monitor_name = %s,
            equipment_set_components.monitor_serial_number = %s,
            equipment_set_components.keyboard_name = %s,
            equipment_set_components.keyboard_serial_number = %s,
            equipment_set_components.mouse_name = %s,
            equipment_set_components.mouse_serial_number = %s,
            equipment_set_components.avr_name = %s,
            equipment_set_components.avr_serial_number = %s,
            equipment_set_components.headset_name = %s,
            equipment_set_components.headset_serial_number = %s
        where
            equipment_set_components.equipment_set_id = %s;
    """

    base_params = (
        sysunit_name,
        sysunit_serial,
        mntr_name,
        mntr_serial,
        kbrd_name,
        kbrd_serial,
        mouse_name,
        mouse_serial,
        avr_name,
        avr_serial,
        hset_name,
        hset_serial,
        id,
    )

    old_data_fetched, old_data = fetch_equipment_component(id)

    equipment_set_component_updated = database.execute_single(base_query, base_params)

    new_data_fetched, new_data = fetch_equipment_component(id)

    if old_data_fetched and new_data_fetched and equipment_set_component_updated['success']:
        account_id = get_jwt_identity()
        logging = log_equipment_set_changes(account_id, id, old_data, new_data)

        if(logging['success']):
            print("Logging component Complete", "- "*50)
    else:
        print("Logging Failed", "! "*50)

    if not equipment_set_component_updated['success']:
        return common_database_error_response(equipment_set_component_updated)

    return common_success_response(
        data=True,
        message="Equipment Components Updated"
    )



# ================================================== HELPER FUNCTIONS

def initialize_equipment_set_components(equipment_set_id:str, data: dict = {}):

    # setup and fetch data
    sysunit_name = data.get('system_unit_name', 'System Unit')
    mntr_name = data.get('monitor_name', 'Monitor')
    kbrd_name = data.get('keyboard_name', 'Keyboard')
    mouse_name = data.get('mouse_name', 'Mouse')
    avr_name = data.get('avr_name', 'AVR Unit')
    hset_name = data.get('headset_name', 'Headset')

    base_query = """
        insert into equipment_set_components
            (
                equipment_set_components.equipment_set_id,
                equipment_set_components.system_unit_name,
                equipment_set_components.monitor_name,
                equipment_set_components.keyboard_name,
                equipment_set_components.mouse_name,
                equipment_set_components.avr_name,
                equipment_set_components.headset_name,
                equipment_set_components.system_unit_serial_number,
                equipment_set_components.monitor_serial_number,
                equipment_set_components.keyboard_serial_number,
                equipment_set_components.mouse_serial_number,
                equipment_set_components.avr_serial_number,
                equipment_set_components.headset_serial_number
            )
        values
            (%s, %s, %s, %s, %s, %s, %s, 'changeme', 'changeme', 'changeme', 'changeme', 'changeme', 'changeme');
    """

    base_params = (
        equipment_set_id,
        sysunit_name,
        mntr_name,
        kbrd_name,
        mouse_name,
        avr_name,
        hset_name,
    )

    equipment_set_component_added = database.execute_single(base_query, base_params)

    if not equipment_set_component_added['success']:
        return False

    return True


# ========== HELPER FUNCTIONS

def fetch_equipment_component(id: str):
    base_query = """
        select
            eq_set_comp.equipment_set_id,
            eq_set_comp.system_unit_name,
            eq_set_comp.system_unit_serial_number,
            eq_set_comp.monitor_name,
            eq_set_comp.monitor_serial_number,
            eq_set_comp.keyboard_name,
            eq_set_comp.keyboard_serial_number,
            eq_set_comp.mouse_name,
            eq_set_comp.mouse_serial_number,
            eq_set_comp.avr_name,
            eq_set_comp.avr_serial_number,
            eq_set_comp.headset_name,
            eq_set_comp.headset_serial_number
        from equipment_set_components as eq_set_comp
        where equipment_set_id = %s;
    """

    # execute query
    equipment_component_fetch = database.fetch_one(base_query, (id, ))

    # query fails
    if not equipment_component_fetch['success']:
        return False, None

    # success
    return True, equipment_component_fetch['data']

