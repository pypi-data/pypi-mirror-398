class UnicatMetadataField:
    """A metadata field can have a value or a reference (asset, field), and it can be
    localized.

    # example field

    artnr = unicat.get_field_by_name("artnr")

    # for values (incl localized)

    meta_align = artnr.metadata["heading.alignment"]
    meta_align.name            # "heading.alignment"
    meta_align.type            # "textline"
    meta_align.is_localized    # False
    meta_align.value           # "left"

    # for localized values

    meta_abbr = artnr.metadata["heading.abbreviation"]
    meta_abbr.name             # "heading.abbreviation"
    meta_abbr.type             # "textline"
    meta_abbr.is_localized     # True
    meta_abbr.value            # {"en": "Artnr", "nl": "Artnr"}
    meta_abbr.value["en"]      # "Artnr"

    # for references

    meta_icon = artnr.metadata["heading.icon"]
    meta_icon.type             # "image"
    meta_icon.is_localized     # False
    meta_icon.value            # UnicatAsset | None
    meta_icon.value.gid        # "a0a80c9c-fa1b-4573-ac98-b7b07c81b583"
    meta_icon.value.pathname   # "/products/cms225.eps"

    meta_related = artnr.metadata["heading.related_field"]
    meta_related.type          # "fieldpicker"
    meta_related.is_localized  # False
    meta_related.value         # UnicatField | None
    meta_related.value.gid     # "0c9ca0a8-fa1b-4573-ac98-81b583b7b07c"
    meta_related.value.name    # "EAN"

    # for localized references

    meta_icon = artnr.metadata["heading.icon"]
    meta_icon.type             # "image"
    meta_icon.is_localized     # True
    meta_icon.value            # {"en": UnicatAsset | None, "nl": UnicatAsset | None}  | None
    meta_icon.value["en"]      # UnicatAsset | None
    meta_icon.value["en"].gid  # "a0a80c9c-fa1b-4573-ac98-b7b07c81b583"
    meta_icon.value["en"].pathname   # "/products/cms225.eps"

    meta_related = artnr.metadata["heading.related_field"]
    meta_related.type             # "fieldpicker"
    meta_related.is_localized     # True
    meta_related.value            # {"en": UnicatField | None, "nl": UnicatField | None} | None
    meta_related.value["en"]      # UnicatField | None
    meta_related.value["en"].gid  # "0c9ca0a8-fa1b-4573-ac98-81b583b7b07c"
    meta_related.value["en"].name # "EAN"
    """

    def __init__(self, unicat, name, metadata_field):
        self._unicat = unicat
        self._name = name
        self._type = metadata_field["type"]
        self._is_localized = metadata_field["is_localized"]
        self._value = metadata_field["value"]

    @property
    def name(self):
        return self._name

    @property
    def type(self):
        return self._type

    @property
    def is_localized(self):
        return self._is_localized

    @property
    def value(self):
        if self.type not in ("image", "fieldpicker"):
            return self._value

        if self.type == "image":
            if self.is_localized:
                return (
                    {
                        language: self._unicat.get_asset(localized_value)
                        for language, localized_value in self._value.items()
                    }
                    if self._value
                    else None
                )

            return self._unicat.get_asset(self._value)

        if self.type == "fieldpicker":
            if self.is_localized:
                return (
                    {
                        language: self._unicat.get_field(localized_value)
                        for language, localized_value in self._value.items()
                    }
                    if self._value
                    else None
                )

            return self._unicat.get_field(self._value)
