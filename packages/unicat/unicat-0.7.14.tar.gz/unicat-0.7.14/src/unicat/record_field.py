from .error import UnicatError


class UnicatRecordField:
    """A record field can have a value, a reference (record, asset), or it can be
    nested for class-fields.
    We also support 'list' versions of these.

    # for values

    artnr = record.fields[language]["artnr"]  # a recordfield
    artnr.value             # "CMS 225-945"
    artnr.field.label       # "Article number"
    artnr.field.type        # "textline"

    for references

    image = record.fields[language]["image"]  # both recordfield and asset
    image.value             # "a0a80c9c-fa1b-4573-ac98-b7b07c81b583"
    image.field.label       # "Image"
    image.pathname          # "/products/cms225.eps"

    for class fields

    dimensions_interior = record.fields[language]["dimensions_interior"]
                            # a recordfield and classfield
    dimensions_interior.value               # {"width__mm": 374, …}
    dimensions_interior["width__mm"].value  # 374  -- this is a recordfield

    # for list values

    colors = record.fields[language]["colors"]
    colors.value            # ["Red", "Blue"]
    colors.field.label      # "Colors"
    colors[0].value         # "Red" -- this is just a string
    colors[0].key           # "r"

    # for list references

    images = record.fields[language]["images"]
    images.value            # ["a0a80c9c-fa1b-4573-ac98-b7b07c81b583", ]
    images.field.label      # "Images"
    images[0]               # this is just an asset
    images[0].pathname      # "/products/cms225.eps"

    for classlist fields

    tablespecs = record.fields[language]["tablespecs"]
    tablespecs.value                        # [{"width__mm": 7, …}, …]
    tablespecs.field.label                  # "Table specs"
    tablespecs[0]                           # this is recordfield-like
    tablespecs[0]["width__mm"].value        # 7
    tablespecs[0]["width__mm"].field.label  # "Width"
    """

    def __init__(self, unicat, record, field, value, key=None):
        self._unicat = unicat
        self._record = record
        self.field = field
        self.value = value
        self.key = key

    def __str__(self):
        return str(self.value)

    def __bool__(self):
        return self.value is not None

    def __getattr__(self, name):
        # used for fluent interface for references
        # lazily loads the record or asset
        if self.field.type == "record":
            ref = self._unicat.get_record(self.value)
            return getattr(ref, name)
        elif self.field.type in ["file", "image"]:
            ref = self._unicat.get_asset(self.value)
            return getattr(ref, name)
        raise AttributeError(name)

    def __getitem__(self, key):
        # used for lists (int key) and class fields (str key)
        if isinstance(key, int):
            if self.value is None:
                raise StopIteration  # so enumerate() keeps working on None too
            if self.field.type == "recordlist":
                refkey = self.value[key]
                try:
                    return self._unicat.get_record(refkey)
                except UnicatError:
                    return None
            elif self.field.type in ("filelist", "imagelist"):
                refkey = self.value[key]
                try:
                    return self._unicat.get_asset(refkey)
                except UnicatError:
                    return None
            elif self.field.type == "classlist":
                classdata = self.value[key]
                return self._get_classfields(classdata)
            return self.value[key]
        elif isinstance(key, str):
            classfields = self._get_classfields(self.value)
            return classfields[key]
        raise KeyError(key)

    def _get_classfields(self, data):
        classfields = {}
        if not data or not self.field.class_:
            return classfields
        from .record_class_field import UnicatRecordClassField

        for field in self.field.class_.fields:
            if field.name.endswith("/key"):
                continue
            classfields[field.name] = UnicatRecordClassField(
                self._unicat,
                self,
                field,
                data[field.name] if field.name in data else None,
                data[field.name + "/key"] if field.name + "/key" in data else None,
            )
        return classfields
