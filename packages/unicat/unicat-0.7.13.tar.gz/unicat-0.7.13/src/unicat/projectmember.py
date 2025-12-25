class UnicatProjectMember:
    def __init__(self, unicat, project_member_data):
        self._unicat = unicat
        self._data = project_member_data

    @property
    def project(self):
        from .project import UnicatProject

        return UnicatProject(self._unicat, self._data["project_gid"])

    @property
    def user(self):
        from .user import UnicatUser

        return UnicatUser(self._unicat, self._data["user_gid"])

    @property
    def status(self):
        return self._data["status"]

    @property
    def roles(self):
        return self._data["roles"]

    @property
    def options(self):
        return self._data["options"]

    @property
    def key(self):
        return self._unicat.api.project_member_key(self._data)
