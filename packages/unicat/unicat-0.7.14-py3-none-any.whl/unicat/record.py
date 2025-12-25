from .record_field import UnicatRecordField


class UnicatRecord:
    def __init__(self, unicat, gid, validation_report=None):
        self._unicat = unicat
        self._data = self._unicat.records[gid]
        fields_by_name = {}
        for field in self.definition.all_fields:
            fields_by_name[field.name] = field
        self._fields = {
            language: {
                fieldname: UnicatRecordField(
                    self._unicat,
                    self,
                    fields_by_name[fieldname],
                    self._data["fields"][language][fieldname],
                    self._data["fields"][language][fieldname + "/key"]
                    if fieldname + "/key" in self._data["fields"][language]
                    else None,
                )
                for fieldname in self._data["fields"][language]
                if not fieldname.endswith("/key")
            }
            for language in self._data["fields"]
        }
        self.validation_report = validation_report

    @property
    def gid(self):
        return self._data["gid"]

    @property
    def canonical(self):
        return self._data["canonical"]

    @property
    def parent(self):
        return self._data["parent"]

    @property
    def backlinks(self):
        return self._data["backlinks"]

    @property
    def is_link(self):
        return self._data["is_link"]

    @property
    def is_deleted(self):
        return self._data["status"] == "deleted"

    @property
    def treelevel(self):
        return self._data["treelevel"]

    @property
    def path(self):
        return self._data["path"]

    @property
    def title(self):
        return self._data["title"]

    @property
    def channels(self):
        return self._data["channels"]

    @property
    def orderings(self):
        return self._data["orderings"]

    @property
    def childcount(self):
        return self._data["childcount"]

    @property
    def definition(self):
        from .definition import UnicatDefinition

        return UnicatDefinition(self._unicat, self._data["definition"])

    @property
    def created_on(self):
        return self._data["created_on"]

    @property
    def updated_on(self):
        return self._data["updated_on"]

    @property
    def fields(self):
        return self._fields
