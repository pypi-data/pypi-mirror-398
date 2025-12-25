from ..class_ import UnicatClass
from ..error import UnicatError
from ..utils import serialize_metadata


def create_class(
    unicat, *, name=None, label=None, fields=None, metadata=None, **kwargs
):
    properties = {**kwargs}
    if name is not None:
        properties["name"] = name
    if label is not None and isinstance(label, dict):
        properties["label"] = label
    if fields is not None and not isinstance(fields, str):
        properties["fields"] = [
            field.gid if hasattr(field, "gid") else field for field in fields
        ]
    if metadata is not None and isinstance(metadata, dict):
        properties["metadata"] = serialize_metadata(metadata)

    success, result = unicat.api.call("/classes/create", properties)
    if not success:
        raise UnicatError("create_class", result)
    return UnicatClass(unicat, result["class"])


def modify_class(
    unicat, class_, *, name=None, label=None, fields=None, metadata=None, **kwargs
):
    properties = {**kwargs}
    if name is not None:
        properties["name"] = name
    if label is not None and isinstance(label, dict):
        properties["label"] = label
    if fields is not None and not isinstance(fields, str):
        properties["fields"] = [
            field.gid if hasattr(field, "gid") else field for field in fields
        ]
    if metadata is not None and isinstance(metadata, dict):
        properties["metadata"] = serialize_metadata(metadata)
    properties["class"] = class_.gid

    success, result = unicat.api.call("/classes/modify", properties)
    if not success:
        raise UnicatError("modify_class", result)
    return UnicatClass(unicat, result["class"])


def modify_class_modify_layout(
    unicat,
    class_,
    *,
    name=None,
    root=None,
    components=None,
):
    layout_properties = {}
    if name is not None:
        layout_properties["name"] = name
    if root is not None:
        layout_properties["root"] = root
    if components is not None and isinstance(components, dict):
        layout_properties["components"] = components
    success, result = unicat.api.call(
        "/classes/layouts/modify",
        {**layout_properties, "class": class_.gid},
    )
    if not success:
        raise UnicatError("modify_class_modify_layout", result)
    return UnicatClass(unicat, result["class"])


def modify_class_add_field(unicat, class_, field):
    success, result = unicat.api.call(
        "/classes/fields/add",
        {"class": class_.gid, "field": field.gid},
    )
    if not success:
        raise UnicatError("modify_class_add_field", result)
    return UnicatClass(unicat, result["class"])


def modify_class_remove_field(unicat, class_, field):
    success, result = unicat.api.call(
        "/classes/fields/remove",
        {"class": class_.gid, "field": field.gid},
    )
    if not success:
        raise UnicatError("modify_class_remove_field", result)
    return UnicatClass(unicat, result["class"])


def modify_class_set_metadata(
    unicat,
    class_,
    name,
    *,
    type=None,
    is_localized=None,
    value=None,
):
    properties = {}
    properties["class"] = class_.gid
    properties["name"] = name
    if type is not None:
        properties["type"] = type
    if is_localized is not None and isinstance(is_localized, bool):
        properties["is_localized"] = is_localized
    if value is not None:
        properties["value"] = value

    success, result = unicat.api.call("/classes/metadata/set", properties)
    if not success:
        raise UnicatError("modify_class_set_metadata", result)
    return UnicatClass(unicat, result["class"])


def modify_class_clear_metadata(
    unicat,
    class_,
    name,
):
    properties = {}
    properties["class"] = class_.gid
    properties["name"] = name

    success, result = unicat.api.call("/classes/metadata/clear", properties)
    if not success:
        raise UnicatError("modify_class_clear_metadata", result)
    return UnicatClass(unicat, result["class"])


def commit_class(unicat, new_or_working_copy):
    success, result = unicat.api.call(
        "/classes/commit", {"class": new_or_working_copy.gid}
    )
    if not success:
        raise UnicatError("commit_class", result)
    if (
        result["class"] != new_or_working_copy.gid
        and new_or_working_copy.gid in unicat.api.data["classes"]
    ):
        del unicat.api.data["classes"][new_or_working_copy.gid]
    return UnicatClass(unicat, result["class"])


def save_as_new_class(unicat, working_copy):
    success, result = unicat.api.call(
        "/classes/save_as_new", {"class": working_copy.gid}
    )
    if not success:
        raise UnicatError("save_as_new_class", result)
    return UnicatClass(unicat, result["class"])


def delete_class(unicat, class_):
    success, result = unicat.api.call("/classes/delete", {"class": class_.gid})
    if not success:
        raise UnicatError("delete_class", result)
    if class_.gid in unicat.api.data["classes"]:
        del unicat.api.data["classes"][class_.gid]
    return True
