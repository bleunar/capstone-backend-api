from flask import Blueprint, jsonify, request
from app.services.jwt import require_access
import app.services.database as database
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.config import config

bp_account_settings = Blueprint("account_settings", __name__)

@bp_account_settings.route("/", methods=["GET"])
@jwt_required()
@require_access("guest")
def get():
    account_id = get_jwt_identity()

    if not is_initialized(account_id):
        return jsonify({
            "msg": "failed to fetch settings, not properly initialized"
        }), 400


    # setup base query
    base_query = """
        select
            acs.account_id,
            acs.enable_dark_mode,
            acs.notification_position,
            acs.notification_duration,
            acs.notification_sound,
            acs.updated_at
        from account_settings as acs
        where acs.account_id = %s;
    """

    # execute query
    account_settings_fetch = database.fetch_all(base_query, (account_id, ))

    # query fails
    if not account_settings_fetch['success']:
        result = jsonify({
            "msg": account_settings_fetch['msg']
        })
        return result, 400

    # success
    return jsonify({
        "data": account_settings_fetch['data'][0]
    }), 200



@bp_account_settings.route("/", methods=["PUT"])
@jwt_required()
def edit():
    
    # fetch current user's identity
    account_id = get_jwt_identity()
    data = request.get_json()

    if not is_initialized(account_id):
        return jsonify({
            "msg": "failed to edit settings, not properly initialized"
        }), 400
    

    # fetch data forms
    enable_dark_mode = data['enable_dark_mode']
    notification_position = data['notification_position']
    notification_duration = data['notification_duration']
    notification_sound = data['notification_sound']

    # prepare query and parameters
    base_query = """
        update account_settings set
            account_settings.enable_dark_mode = %s,
            account_settings.notification_position = %s,
            account_settings.notification_duration = %s,
            account_settings.notification_sound = %s
        where
            account_settings.account_id = %s;
    """

    base_params = (enable_dark_mode, notification_position, notification_duration, notification_sound, account_id)

    account_settings_updated = database.execute_single(base_query, base_params)

    if not account_settings_updated['success']:
        result = jsonify({
            "msg": account_settings_updated['msg']
        })
        return result, 400

    result = jsonify({
        "data": True
    })
    return result, 200




# check for initialized data
def is_initialized(account_id: str):
    
    # check if there is an existing record for the account
    record_checked = database.fetch_scalar(
        """
            select account_settings.account_id from account_settings where account_settings.account_id = %s
        """,
        (account_id, )
    )
    if record_checked['success'] and record_checked['data']: return True
    else:

        # initialize data
        base_query = """
            insert into account_settings
                (
                    account_settings.account_id,
                    account_settings.enable_dark_mode,
                    account_settings.notification_position,
                    account_settings.notification_duration,
                    account_settings.notification_sound
                )
            values
                (%s, 1, ' top-0 start-50 translate-middle-x ', '4', 'full');
        """
        base_params = (account_id, )

        insert_status = database.execute_single(base_query, base_params)

        if insert_status['success']:
            return True
        else:
            return False