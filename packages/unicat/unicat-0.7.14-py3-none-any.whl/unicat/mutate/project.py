from ..error import UnicatError
from ..utils import _job


def add_language(unicat, language):
    success, result = unicat.api.call("/languages/add", {"language": language})
    if not success:
        raise UnicatError("add_language", result)
    return True


def remove_language(unicat, language):
    success, result = unicat.api.call("/languages/remove", {"language": language})
    if not success:
        raise UnicatError("remove_language", result)
    return True


def create_channel(unicat, name):
    success, result = unicat.api.call("/channels/create", {"name": name})
    if not success:
        raise UnicatError("create_channel", result)
    return result["channel"]


def delete_channel(unicat, channel_gid):
    success, result = unicat.api.call("/channels/delete", {"channel": channel_gid})
    if not success:
        raise UnicatError("delete_channel", result)
    return True


def create_ordering(unicat, name):
    success, result = unicat.api.call("/orderings/create", {"name": name})
    if not success:
        raise UnicatError("create_ordering", result)
    return result["ordering"]


def delete_ordering(unicat, ordering_gid):
    success, result = unicat.api.call("/orderings/delete", {"ordering": ordering_gid})
    if not success:
        raise UnicatError("delete_ordering", result)
    return True


def create_fieldlist(unicat, name):
    success, result = unicat.api.call("/fieldlists/create", {"name": name})
    if not success:
        raise UnicatError("create_fieldlist", result)
    return result["fieldlist"]


def delete_fieldlist(unicat, fieldlist_gid):
    success, result = unicat.api.call(
        "/fieldlists/delete", {"fieldlist": fieldlist_gid}
    )
    if not success:
        raise UnicatError("delete_fieldlist", result)
    return True


@_job
def create_backup(unicat, created_by, name=None):
    # becomes create_backup(unicat, created_by, name=None, *, return_job=False): UnicatProjectBackup | UnicatJob
    params = {"created_by": created_by}
    if name is not None:
        params["name"] = name
    success, result = unicat.api.call("/backups/create", params)
    if not success:
        raise UnicatError("create_backup", result)
    return result["job.token"], unicat.project.get_backup(result["version"])


def update_backup(unicat, backup, name):
    success, result = unicat.api.call(
        "/backups/update", {"version": backup.version, "name": name}
    )
    if not success:
        raise UnicatError("update_backup", result)
    return unicat.project.get_backup(result["version"])


@_job
def restore_backup(unicat, backup):
    # becomes restore_backup(unicat, version, *, return_job=False): UnicatProject | UnicatJob
    success, result = unicat.api.call("/backups/restore", {"version": backup.version})
    if not success:
        raise UnicatError("restore_backup", result)
    return result["job.token"], unicat.project


def delete_backup(unicat, backup):
    success, result = unicat.api.call("/backups/delete", {"version": backup.version})
    if not success:
        raise UnicatError("delete_backup", result)
    return unicat.project


def delete_backups(unicat, backups):
    success, result = unicat.api.call(
        "/backups/delete", {"versions": [backup.version for backup in backups]}
    )
    if not success:
        raise UnicatError("delete_backups", result)
    return unicat.project
