from ..error import UnicatError
from ..query import UnicatQuery


def create_query(unicat, type, *, name, q=None, filter=None):
    properties = {}
    if type is not None and type in ("record", "asset", "schema"):
        properties["type"] = type
    if name is not None:
        properties["name"] = name
    if q is not None:
        properties["q"] = q
    if filter is not None and isinstance(filter, (list, tuple)):
        properties["filter"] = filter
    success, result = unicat.api.call("/queries/create", properties)
    if not success:
        raise UnicatError("create_query", result)
    return UnicatQuery(unicat, result["query"])


def update_query(unicat, query, *, name=None, q=None, filter=None):
    properties = {}
    if name is not None:
        properties["name"] = name
    if q is not None:
        properties["q"] = q
    if filter is not None and isinstance(filter, (list, tuple)):
        properties["filter"] = filter
    properties["query"] = query.gid
    success, result = unicat.api.call("/queries/update", properties)
    if not success:
        raise UnicatError("update_query", result)
    return UnicatQuery(unicat, result["query"])


def delete_query(unicat, query):
    success, result = unicat.api.call("/queries/delete", {"query": query.gid})
    if not success:
        raise UnicatError("delete_query", result)
    if query.gid in unicat.api.data["queries"]:
        del unicat.api.data["queries"][query.gid]
    return True
