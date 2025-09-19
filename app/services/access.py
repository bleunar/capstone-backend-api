import json, os

def get_access_levels():
    base = os.path.dirname(__file__)
    path = os.path.join(base, "access_levels.json")
    with open(path, 'r') as f:
        data_as_dict = json.load(f)
    return data_as_dict


def access_level_lookup():
    base = os.path.dirname(__file__)
    path = os.path.join(base, "access_levels.json")
    with open(path, 'r') as f:
        data_dict = json.load(f)

    access_level_dict = {}
    for item in data_dict:
        access_level_dict[(item['codename'])] = item['id']

    return access_level_dict