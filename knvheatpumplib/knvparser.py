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


def get_val_ids_by_func_group(code):
    """
    Returns a set of partial var ids by function group
    """
    if code["functiongroupId"] == 100:
        return [0, 2, 3, 5, 6, 9, 10, 11, 12, 13, 15, 16, 101]
    elif code["functiongroupId"] == 101:
        return [0, 1, 2, 3, 5, 6, 7, 20]
    elif code["functiongroupId"] == 110:
        return [0]
    elif code["functiongroupId"] == 120 and code["functionId"] == 0:
        return [0, 2, 8, 45, 56]
    elif code["functiongroupId"] == 180 and code["functionId"] == 1:
        return [103]
    elif code["functiongroupId"] == 190:
        return [0, 1, 2, 3]
    else:
        return []


def gen_func_id(code):
    """
    Generates function ids
    """
    return str(code["unitId"]) + "." + str(code["functiongroupId"]) + "." + str(code["functionId"])


def gen_func_val_ids(code):
    """
    Generates for every function a set of Variables IDs
    """

    const_var = get_val_ids_by_func_group(code)

    result = []

    for var in const_var:
        result.append(gen_func_id(code) + "." + str(var))

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


def set_vm_value(id, val):
    """
    Generated setVMValue command string
    """
    return command("setVMValue", {
        "dap": id,
        "value": str(val)
    })


def get_all_ids():
    """Returns base id list"""
    list_func = []

    list_func.extend(gen_func_val_ids(
        {"functionId": 0, "functiongroupId": 120, "unitId": 1}
    ))

    list_func.extend(gen_func_val_ids(
        {"functionId": 1, "functiongroupId": 180, "unitId": 1}
    ))

    list_func.extend(gen_func_val_ids(
        {"functionId": 51, "functiongroupId": 190, "unitId": 1}
    ))

    list_func.append("1.110.2.0")
    list_func.append("1.110.3.0")
    list_func.append("1.110.5.0")

    list_func.append("1.120.1.2")

    return list_func
