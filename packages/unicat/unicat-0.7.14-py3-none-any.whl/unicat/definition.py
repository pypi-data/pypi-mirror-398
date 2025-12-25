from .metadata_field import UnicatMetadataField


class UnicatDefinition:
    def __init__(self, unicat, gid):
        self._unicat = unicat
        self._data = self._unicat.definitions[gid]

    @property
    def gid(self):
        return self._data["gid"]

    @property
    def original(self):
        if not self._data["original"]:
            return None
        if self.is_new:
            return None
        return UnicatDefinition(self._unicat, self._data["original"])

    @property
    def name(self):
        return self._data["name"]

    @property
    def label(self):
        return self._data["label"]

    @property
    def classes(self):
        from .class_ import UnicatClass

        return [UnicatClass(self._unicat, gid) for gid in self._data["classes"]]

    @property
    def classes_as_gids(self):
        return self._data["classes"]

    @property
    def fields(self):
        from .field import UnicatField

        return [UnicatField(self._unicat, gid) for gid in self._data["fields"]]

    @property
    def fields_as_gids(self):
        return self._data["fields"]

    @property
    def titlefield(self):
        from .field import UnicatField

        return UnicatField(self._unicat, self._data["titlefield"])

    @property
    def fieldlists(self):
        from .field import UnicatField

        return {
            key: [UnicatField(self._unicat, gid) for gid in value]
            for key, value in self._data["fieldlists"].items()
        }

    @property
    def layout(self):
        from .layout import UnicatLayout

        return UnicatLayout(self._unicat, self._data["layout"])

    @property
    def childdefinitions(self):
        return [
            UnicatDefinition(self._unicat, gid)
            for gid in self._data["childdefinitions"]
        ]

    @property
    def is_base(self):
        return self._data["is_base"]

    @property
    def is_new(self):
        return self._data["is_new"]

    @property
    def is_working_copy(self):
        return self._data["is_working_copy"]

    @property
    def is_extended(self):
        return self._data["is_extended"]

    @property
    def is_committed(self):
        return not self._data["is_new"] and not self._data["is_working_copy"]

    @property
    def all_fields(self):
        """All fields, including those from classes"""
        fields = []
        fields.extend(self.fields)
        for class_ in self.classes:
            fields.extend(class_.fields)
        return fields

    @property
    def all_base_fields(self):
        """All base fields, including those from base classes"""
        if not self.is_extended:
            fields = []
            fields.extend(self.fields)
            for class_ in self.classes:
                fields.extend(class_.fields)
            return fields
        else:
            return self.original.all_base_fields

    @property
    def all_extended_fields(self):
        """All extended fields, including those from extended classes"""
        if not self.is_extended:
            return []
        else:
            base_field_gids = [field.gid for field in self.all_base_fields]
            fields = []
            for class_ in self.classes:
                fields.extend(
                    [
                        field
                        for field in class_.fields
                        if field.gid not in base_field_gids
                    ]
                )
            fields.extend(
                [field for field in self.fields if field.gid not in base_field_gids]
            )
            return fields

    @property
    def base_fields(self):
        """Base fields, excluding those from classes"""
        if not self.is_extended:
            return self.fields
        else:
            return self.original.fields

    @property
    def extended_fields(self):
        """Extended fields, excluding those from classes"""
        if not self.is_extended:
            return []
        else:
            base_field_gids = [field.gid for field in self.base_fields]
            fields = [
                field for field in self.fields if field.gid not in base_field_gids
            ]
            return fields

    @property
    def base_classes(self):
        if not self.is_extended:
            return self.classes
        else:
            return self.original.classes

    @property
    def extended_classes(self):
        if not self.is_extended:
            return []
        else:
            base_class_gids = [class_.gid for class_ in self.base_classes]
            classes = [
                class_ for class_ in self.classes if class_.gid not in base_class_gids
            ]
            return classes

    @property
    def metadata(self):
        metadata = {}
        for name, metadata_field in self._data["metadata"].items():
            metadata[name] = UnicatMetadataField(self._unicat, name, metadata_field)
        return metadata
