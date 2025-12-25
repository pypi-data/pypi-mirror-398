from .record_field import UnicatRecordField


class UnicatRecordClassField:
    """A record class field behaves like a UnicatRecordField, but instead of a
    reference to the record, it holds a reference to its parent (class) field.
    """

    def __init__(self, unicat, parentfield, field, value, key=None):
        self._unicat = unicat
        self.parentfield = parentfield
        self.field = field
        self.value = value
        self.key = key

    def __str__(self):
        return UnicatRecordField.__str__(self)

    def __bool__(self):
        return UnicatRecordField.__bool__(self)

    def __getattr__(self, name):
        return UnicatRecordField.__getattr__(self, name)

    def __getitem__(self, key):
        return UnicatRecordField.__getitem__(self, key)

    def _get_classfields(self, data):
        return UnicatRecordField._get_classfields(self, data)
