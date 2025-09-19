from flask import Blueprint, jsonify, request
from app.services.access import get_access_levels, access_level_lookup
from flask_jwt_extended import jwt_required, get_jwt

access_levels_bp = Blueprint("access_level", __name__)

@access_levels_bp.route("/", methods=["GET"])
@jwt_required()
def get():
    access_levels = get_access_levels()
    access_levels_map = access_level_lookup()

    user_access_level = get_jwt().get("acc")
    user_non_root = user_access_level > 0 and request.args.get("codename") == 'root'


    try:
        if 'codename' in request.args:
            
            if user_non_root:
                return jsonify({
                    "msg": "access denied"
                }), 400
            
            result = jsonify({
                access_levels[access_levels_map[(request.args.get("codename"))]]
            })
            return result, 200
        

        if 'id' in request.args:
            if user_non_root:
                return jsonify({
                    "msg": "access denied"
                }), 400
    
            result = jsonify({
                'data': access_levels[int(request.args.get("id"))]
            })
            return result, 200

        if user_non_root:
            access_levels.pop(0)

        return jsonify({
            "data": access_levels
        }), 200
    
    except Exception as e:
        return jsonify({
            "msg": "failed to fetch access levels"
        }), 400