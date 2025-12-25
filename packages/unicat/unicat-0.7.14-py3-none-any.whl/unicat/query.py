class UnicatQuery:
    def __init__(self, unicat, gid):
        self._unicat = unicat
        self._data = self._unicat.queries[gid]

    @property
    def gid(self):
        return self._data["gid"]

    @property
    def type(self):
        return self._data["type"]

    @property
    def name(self):
        return self._data["name"]

    @property
    def q(self):
        return self._data["q"]

    @property
    def filter(self):
        return self._data["filter"]
