from flask import Blueprint, jsonify, request
from services.jwt import require_access
from services.security import generate_id
import services.database as database
from flask_jwt_extended import jwt_required
from config import config

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
            eq_set_comp.camera_name,
            eq_set_comp.camera_serial_number,
        from equipment_set_components as eq_set_comp
        where equipment_set_id = %s;
    """

    # execute query
    equipment_set_components_fetch = database.fetch_one(base_query, (id, ))

    # query fails
    if not equipment_set_components_fetch['success']:
        result = jsonify({
            "msg": equipment_set_components_fetch['msg']
        })
        return result, 400

    # success
    return jsonify({
        "data": equipment_set_components_fetch['data']
    }), 200



@bp_equipment_set_components.route("/<id>", methods=["PUT"])
@require_access('default')
def edit(id):
    data = request.get_json()

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

    cam_name = data.get('camera_name', '')
    cam_serial = data.get('camera_serial_number', '')
    
    
    if any(item is None for item in [sysunit_serial, mntr_serial, kbrd_serial, mouse_serial, sysunit_name, mntr_name, kbrd_name, mouse_name ]):
        return jsonify({
            "msg": "forms data incomplete"
        }), 400


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
            equipment_set_components.headset_serial_number = %s,
            equipment_set_components.camera_name = %s,
            equipment_set_components.camera_serial_number = %s
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
        cam_name,
        cam_serial,
        id,
    )

    equipment_set_component_updated = database.execute_single(base_query, base_params)

    if not equipment_set_component_updated['success']:
        result = jsonify({
            "msg": equipment_set_component_updated['msg']
        })
        return result, 400

    result = jsonify({
        "data": True
    })
    return result, 200



# HELPER FUNCTIONS
def initialize_equipment_set_components(equipment_set_id:str, data: dict):

    # setup and fetch data
    sysunit_name = data.get('system_unit_name', '')
    sysunit_serial = data.get('system_unit_serial_number', '')

    mntr_name = data.get('monitor_name', '')
    mntr_serial = data.get('monitor_serial_number', '')

    kbrd_name = data.get('keyboard_name', '')
    kbrd_serial = data.get('keyboard_serial_number', '')

    mouse_name = data.get('mouse_name', '')
    mouse_serial = data.get('mouse_serial_number', '')

    avr_name = data.get('avr_name', '')
    avr_serial = data.get('avr_serial_number')

    hset_name = data.get('headset_name', '')
    hset_serial = data.get('headset_serial_number', '')

    cam_name = data.get('camera_name', '')
    cam_serial = data.get('camera_serial_number', '')


    if any(item is None for item in [sysunit_serial, mntr_serial, kbrd_serial, mouse_serial, avr_serial, hset_serial, cam_serial ]):
        return jsonify({
            "msg": "forms data incomplete"
        }), 400

    base_query = """
        insert into equipment_set_components
            (
                equipment_set_components.equipment_set_id,
                equipment_set_components.system_unit_name,
                equipment_set_components.system_unit_serial_number,
                equipment_set_components.monitor_name,
                equipment_set_components.monitor_serial_number,
                equipment_set_components.keyboard_name,
                equipment_set_components.keyboard_serial_number,
                equipment_set_components.mouse_name,
                equipment_set_components.mouse_serial_number,
                equipment_set_components.avr_name,
                equipment_set_components.avr_serial_number,
                equipment_set_components.headset_name,
                equipment_set_components.headset_serial_number,
                equipment_set_components.camera_name,
                equipment_set_components.camera_serial_number,
            )
        values
            (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
    """
    base_params = (
        equipment_set_id,
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
        cam_name,
        cam_serial
    )

    equipment_set_component_added = database.execute_single(base_query, base_params)

    if not equipment_set_component_added['success']:
        return False

    return True