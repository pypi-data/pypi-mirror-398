from ..error import UnicatError
from ..module import UnicatModule


def register_module(unicat, name, version):
    success, result = unicat.api.call(
        "/modules/register", {"module": name, "version": version}
    )
    if not success:
        raise UnicatError("register_module", result)
    return UnicatModule(unicat, result["module"])


def unregister_module(unicat, module):
    success, result = unicat.api.call("/modules/unregister", {"module": module.name})
    if not success:
        raise UnicatError("unregister_module", result)
    if module.name in unicat.api.data["modules"]:
        del unicat.api.data["modules"][module.name]
    return True


def set_module_key(unicat, module, key, value):
    success, result = unicat.api.call(
        "/modules/keys/set", {"module": module.name, "key": key, "value": value}
    )
    if not success:
        raise UnicatError("set_module_key", result)
    return UnicatModule(unicat, result["module"])


def set_module_keys(unicat, module, keyvalues):
    success, result = unicat.api.call(
        "/modules/keys/set", {"module": module.name, "keys": keyvalues}
    )
    if not success:
        raise UnicatError("set_module_keys", result)
    return UnicatModule(unicat, result["module"])


def clear_module_key(unicat, module, key):
    success, result = unicat.api.call(
        "/modules/keys/clear", {"module": module.name, "key": key}
    )
    if not success:
        raise UnicatError("clear_module_key", result)
    return UnicatModule(unicat, result["module"])


def clear_module_keys(unicat, module, keys):
    success, result = unicat.api.call(
        "/modules/keys/clear", {"module": module.name, "keys": keys}
    )
    if not success:
        raise UnicatError("clear_module_keys", result)
    return UnicatModule(unicat, result["module"])


def publish_module_action(unicat, module, action, configuration):
    success, result = unicat.api.call(
        "/modules/actions/publish",
        {"module": module.name, "action": action, "configuration": configuration},
    )
    if not success:
        raise UnicatError("publish_module_action", result)
    return UnicatModule(unicat, result["module"])


def unpublish_module_action(unicat, module, action):
    success, result = unicat.api.call(
        "/modules/actions/unpublish", {"module": module.name, "action": action}
    )
    if not success:
        raise UnicatError("unpublish_module_action", result)
    return UnicatModule(unicat, result["module"])


def add_module_log(
    unicat,
    module,
    version,
    *,
    action=None,
    configuration=None,
    command=None,
    started_at=None,
    ended_at=None,
    status=None,
    output=None,
):
    values = {
        "action": action,
        "configuration": configuration,
        "command": command,
        "started_at": started_at,
        "ended_at": ended_at,
        "status": status,
        "output": output,
    }
    keys = list(values.keys())
    for key in keys:
        if values[key] is None:
            del values[key]
    if action is not None:
        values["action"] = action
    success, result = unicat.api.call(
        "/modules/logs/add", {"module": module.name, "version": version, **values}
    )
    if not success:
        raise UnicatError("add_module_log", result)
    return UnicatModule(unicat, result["module"])
