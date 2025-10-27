from flask import Blueprint, jsonify, request
from ..services.jwt import require_access
from ..services.security import generate_id
from ..services import database
from flask_jwt_extended import jwt_required
from ..config import config
from ..services.validation import check_json_payload, check_required_fields, common_error_response, common_success_response, common_database_error_response

bp_locations = Blueprint("locations", __name__)

@bp_locations.route("/", methods=["GET"])
@jwt_required()
@require_access("guest")
def get():
    # setup base query
    base_query = """
        select
            loc.id,
            loc.name,
            loc.description,
            loc.created_at,
            loc.updated_at
        from locations as loc
    """

    # CONDITIONALS
    conditional_query = []
    conditional_params = []


    # filter by id
    if 'id' in request.args and request.args.get('id'):
        conditional_query.append("loc.id = %s")
        conditional_params.append(request.args.get('id'))


    # filter by search
    if 'name' in request.args:
        conditional_query.append("loc.name = %s")
        conditional_params.append(request.args.get('name'))

    # build conditional query
    if conditional_query:
        base_query += " WHERE " + " AND ".join(conditional_query)

    base_query += f" ORDER BY loc.name ASC"
    
    # closing statements
    base_query += ";"

    # execute query
    locations_fetch = database.fetch_all(base_query, tuple(conditional_params))

    # query fails
    if not locations_fetch['success']:
        return common_database_error_response(locations_fetch)
    
    # success
    return common_success_response(locations_fetch['data'])


@bp_locations.route("/", methods=["POST"])
@require_access('admin')
def add():
    # Validate JSON payload
    data, error_response = check_json_payload()
    if error_response:
        return error_response

    # Validate required fields
    required_fields = ['name', 'description']
    validation_error = check_required_fields(data, required_fields)
    if validation_error:
        return validation_error

    # setup and fetch data
    name = data['name']
    description = data['description']

    if not location_name_unique(name):
        return common_error_response(
            message="Location name already exist"
        )
    
    base_query = """
        insert into locations
            (
                locations.id,
                locations.name,
                locations.description
            )
        values
            (%s, %s, %s);
    """
    base_params = (
        generate_id(),
        name,
        description
    )

    location_added = database.execute_single(base_query, base_params)

    if not location_added['success']:
        return common_database_error_response(location_added)

    return common_success_response(data=True)




@bp_locations.route("/<id>", methods=["PUT"])
@require_access('admin')
def edit(id):
    data, error_response = check_json_payload()
    if error_response:
        return error_response

    # fetch data forms
    name = data['name']
    description = data['description']

    if not location_name_unique(name):
        return common_error_response(
            message="Location name already exist"
        )
    
    if any(item is None for item in [name, description]):
        return common_error_response(
            message="Form Data Incomplete"
        )

    # prepare query and parameters
    base_query = """
        update locations set
            locations.name = %s,
            locations.description = %s
        where
            locations.id = %s
    """

    base_params = (name, description, id)

    location_updated = database.execute_single(base_query, base_params)

    if not location_updated['success']:
        common_database_error_response(location_updated)

    return common_success_response(data=True)


# hard delete
@bp_locations.route("/<id>", methods=["DELETE"])
@require_access('admin')
def delete(id):

    # prepare query and parameters
    base_query = """
        delete from locations
        where
            locations.id = %s;
    """
    base_params = (id, )

    # execute query
    location_deleted = database.execute_single(base_query, base_params)

    # if fail
    if not location_deleted['success']:
        common_database_error_response(location_deleted)

    # confirm deletion
    return common_success_response(data=True)


# ANALYTICSSSSS ==================================================================

@bp_locations.route("/analytics/total", methods=["GET"])
def analytics_total():
    query = """
        SELECT COUNT(id) AS data
        FROM locations;
    """

    # execute query
    locations_analytics_fetch_total = database.fetch_scalar(query)

    # query fails
    if not locations_analytics_fetch_total['success']:
        return common_database_error_response(locations_analytics_fetch_total)
    
    # success
    return common_success_response(locations_analytics_fetch_total['data'])


def location_name_unique(name: str):
    base_query = """
        select
            loc.id
        from locations as loc
        where loc.name = %s;
    """

    locations_fetch = database.fetch_all(base_query, (name, ))

    print(name)

    if not locations_fetch['success']:
        return None
    
    return len(locations_fetch['data']) == 0