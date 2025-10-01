from flask import Blueprint, jsonify, request
from app.services.access import get_access_levels, access_level_lookup
from flask_jwt_extended import jwt_required, get_jwt
from app.services.validation import common_success_response, common_error_response

access_levels_bp = Blueprint("access_level", __name__)

@access_levels_bp.route("/", methods=["GET"])
@jwt_required()
def get():
    access_levels = get_access_levels()
    access_levels_map = access_level_lookup()

    user_access_level = get_jwt().get("acc")
    user_non_root = user_access_level > 0 and request.args.get("codename") == 'root'


    try:
        if 'codename' in request.args and request.args.get("codename"):
            
            if user_non_root:
                return common_error_response("Access denied", 403)
            
            codename = request.args.get("codename")
            data = access_levels[access_levels_map[(codename)]]

            if codename and data:
                return common_success_response(data)
            else:
                return common_error_response("Codename not found", 404)

        

        if 'id' in request.args and request.args.get("id"):
            if user_non_root:
                return common_error_response("Access denied", 403)
            
            id_args = request.args.get("id")
            
            # Validate ID parameter
            if not id_args or not id_args.isdigit():
                return common_error_response("Invalid ID parameter. Must be a positive integer.", 400)
            
            try:
                id_index = int(id_args)
                if id_index < 0 or id_index >= len(access_levels):
                    return common_error_response("Access level ID not found", 404)
                
                data = access_levels[id_index]
                return common_success_response(data)
            except (ValueError, IndexError):
                return common_error_response("Invalid access level ID", 400)

        if user_non_root:
            access_levels.pop(0)

        return common_success_response(access_levels)
    
    except Exception as e:
        return common_error_response(f"Failed to fetch access levels: {str(e)}", 500)