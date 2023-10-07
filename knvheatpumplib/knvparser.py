"""
Parsing tools for the websocket
"""
import json
import logging

logger = logging.getLogger()


def ws2json(ws):
    """
    Parses a Websocket response to json
    """
    return json.loads(ws[1:-1])


def json2ws(code):
    """
    Parses a Websocket request to json
    """
    return "#" + json.dumps(code) + "\n"


def get_val_ids_by_func_group(group):
    """
    Returns a set of partiall var ids by function group
    """
    if group == 100:
        return [0, 5, 6, 100, 2, 3, 201, 202]
    elif group == 101:
        return [0, 1, 5, 6, 20]
    else:
        return []


def gen_func_val_ids(code):
    """
    Generates for every function a set of Variables IDs
    """

    const_var = get_val_ids_by_func_group(code["functiongroupId"])

    result = []

    for var in const_var:
        result.append(str(code["unitId"]) + "." + str(code["functiongroupId"]) +
                      "." + str(code["functionId"]) + "." + str(var))

    return result


def command(code, parameter=None):
    """Command parser for KNV

    Args:
        code (string): Command type
        parameter (json, optional): Parameters for the command (if applicable). Defaults to None.

    Returns:
        string: Parsed Command
    """
    if parameter is None:
        return json2ws({
            "command": code
        })
    else:
        return json2ws({
            "command": code,
            "parameter": parameter
        })


def login(username, password):
    """Login Command for KNV

    Args:
        username (string): Username for KNV Home
        password (string): Password for KNV Home

    Returns:
        string: Parsed Command
    """
    return command("login", {
        "username": username,
        "password": password
    })


def get_list_functions(list_id, typ):
    """
    Generates the getListFunctions command string
    """
    return command("getListFunctions", {
        "listId": list_id,
        "type": typ
    })


def add_hotlink(var_id):
    """
    Generated addHotlink command string
    """
    return command("addHotlink", {
        "dap": var_id
    })
