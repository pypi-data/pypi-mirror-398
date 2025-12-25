from .metadata_field import UnicatMetadataField


class UnicatClass:
    def __init__(self, unicat, gid):
        self._unicat = unicat
        self._data = self._unicat.classes[gid]

    @property
    def gid(self):
        return self._data["gid"]

    @property
    def original(self):
        if not self._data["original"]:
            return None
        if self.is_new:
            return None
        return UnicatClass(self._unicat, self._data["original"])

    @property
    def name(self):
        return self._data["name"]

    @property
    def label(self):
        return self._data["label"]

    @property
    def fields(self):
        from .field import UnicatField

        return [UnicatField(self._unicat, gid) for gid in self._data["fields"]]

    @property
    def fields_as_gids(self):
        return self._data["fields"]

    @property
    def layout(self):
        from .layout import UnicatLayout

        return UnicatLayout(self._unicat, self._data["layout"])

    @property
    def is_new(self):
        return self._data["is_new"]

    @property
    def is_working_copy(self):
        return self._data["is_working_copy"]

    @property
    def is_committed(self):
        return not self._data["is_new"] and not self._data["is_working_copy"]

    @property
    def metadata(self):
        metadata = {}
        for name, metadata_field in self._data["metadata"].items():
            metadata[name] = UnicatMetadataField(self._unicat, name, metadata_field)
        return metadata
