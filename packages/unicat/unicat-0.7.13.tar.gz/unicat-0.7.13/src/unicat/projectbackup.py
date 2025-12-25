class UnicatProjectBackup:
    def __init__(self, unicat, project_gid, backup):
        self._unicat = unicat
        self._project = self._unicat.projects[project_gid]
        self._data = backup

    @property
    def version(self):
        return self._data["version"]

    @property
    def name(self):
        return self._data["name"]

    @property
    def created_by(self):
        return self._data["created_by"]

    @property
    def timestamp(self):
        return self._data["timestamp"]
