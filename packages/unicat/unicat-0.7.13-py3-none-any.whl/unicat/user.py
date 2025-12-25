# from .project import UnicatProject


class UnicatUser:
    def __init__(self, unicat, gid):
        self._unicat = unicat
        self._data = self._unicat.users[gid]

    @property
    def gid(self):
        return self._data["gid"]

    @property
    def username(self):
        return self._data["username"]

    @property
    def name(self):
        return self._data["name"]

    @property
    def avatar(self):
        return self._data["avatar"]
