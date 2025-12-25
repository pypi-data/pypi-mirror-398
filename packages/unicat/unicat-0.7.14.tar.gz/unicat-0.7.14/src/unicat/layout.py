class UnicatLayout:
    def __init__(self, unicat, gid):
        self._unicat = unicat
        self._data = self._unicat.layouts[gid]

    @property
    def gid(self):
        return self._data["gid"]

    @property
    def original(self):
        if not self._data["original"]:
            return None
        return UnicatLayout(self._unicat, self._data["original"])

    @property
    def name(self):
        return self._data["name"]

    @property
    def root(self):
        return self._data["root"]

    @property
    def components(self):
        return self._data["components"]

    @property
    def is_new(self):
        return self._data["is_new"]

    @property
    def is_working_copy(self):
        return self._data["is_working_copy"]
