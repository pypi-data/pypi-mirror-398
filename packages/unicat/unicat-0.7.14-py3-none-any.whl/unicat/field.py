from .metadata_field import UnicatMetadataField


class UnicatField:
    def __init__(self, unicat, gid):
        self._unicat = unicat
        self._data = self._unicat.fields[gid]

    @property
    def gid(self):
        return self._data["gid"]

    @property
    def original(self):
        if not self._data["original"]:
            return None
        if self.is_new:
            return None
        return UnicatField(self._unicat, self._data["original"])

    @property
    def name(self):
        return self._data["name"]

    @property
    def type(self):
        return self._data["type"]

    @property
    def class_(self):
        if self._data["type"] not in ("class", "classlist"):
            return None
        if "class" not in self._data["options"] or not self._data["options"]["class"]:
            return None

        from .class_ import UnicatClass

        return UnicatClass(self._unicat, self._data["options"]["class"])

    @property
    def options(self):
        return self._data["options"]

    @property
    def is_localized(self):
        return self._data["is_localized"]

    @property
    def is_required(self):
        return self._data["is_required"]

    @property
    def label(self):
        return self._data["label"]

    @property
    def initial(self):
        return self._data["initial"]

    @property
    def unit(self):
        return self._data["unit"]

    @property
    def title(self):
        if not self.unit:
            return self.label
        return {
            language: f"{label} [{self.unit}]" for language, label in self.label.items()
        }

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
