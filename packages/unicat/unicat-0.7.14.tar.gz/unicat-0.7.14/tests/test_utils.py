import pytest

from unicat.metadata_field import UnicatMetadataField
from unicat.utils import (
    DuckObject,
    convert_fielddata_to_value,
    convert_value_to_fielddata,
    diff_record_fields_data,
    gid,
    hash_data,
    hash_text,
    maybe_dotted_gid,
    maybe_gid,
    merge_dicts,
    serialize_metadata,
)
from unicat.utils import (
    test_false as alias_test_false,  # alias for pytest, can't start with test_
)
from unicat.utils import (
    test_true as alias_test_true,  # alias for pytest, can't start with test_
)


def test_gid():
    key = gid()
    assert isinstance(key, str)
    assert maybe_gid(key)
    assert not maybe_gid(key[1:])
    assert not maybe_gid(key[:-1])
    assert not maybe_gid(key + "1")
    assert not maybe_gid("1" + key)
    assert not maybe_gid(123)


def test_dotted_gid():
    key = gid()
    dotted_key = key + "." + gid()
    assert isinstance(dotted_key, str)
    assert maybe_dotted_gid(dotted_key)
    assert maybe_dotted_gid(dotted_key + "." + gid())
    assert maybe_dotted_gid(key)  # single gid is ok
    assert not maybe_dotted_gid(dotted_key[1:])
    assert not maybe_dotted_gid(dotted_key[:-1])
    assert not maybe_dotted_gid(dotted_key + "1")
    assert not maybe_dotted_gid("1" + dotted_key)
    assert not maybe_dotted_gid(123)


def test_true_false():
    assert alias_test_false(False)
    assert alias_test_true(True)
    for false in (
        "",
        "0",
        "no",
        "n",
        "nee",
        "nein",
        "non",
        "off",
        "false",
        "f",
        "unchecked",
        "deselected",
        "none",
        "nil",
        "null",
        "undefined",
    ):
        assert alias_test_false(false)
        assert not alias_test_true(false)
    assert alias_test_true("on")
    assert alias_test_true("yes")
    assert alias_test_true(1)
    assert alias_test_true("anything-not-falsey")


def test_duck_object():
    ducklike = DuckObject(walk="waddle", talk="quack")
    assert ducklike.walk == "waddle"
    assert ducklike.talk == "quack"
    assert not hasattr(ducklike, "bill")


@pytest.mark.skip(
    reason="no way of currently testing this without actual Unicat connection"
)
def test_field_columns():
    assert True


def test_convert_value_to_fielddata():
    assert convert_value_to_fielddata("text", "123") == "123"
    assert convert_value_to_fielddata("textline", "123") == "123"
    assert convert_value_to_fielddata("textline", 123) == "123"
    assert convert_value_to_fielddata("textlist", "123\n456") == ["123", "456"]
    assert convert_value_to_fielddata("number", "123") == 123
    assert convert_value_to_fielddata("decimal", "123") == 123
    assert convert_value_to_fielddata("decimal", "123.45") == 123.45
    assert convert_value_to_fielddata("decimal", "123,45") == 123.45
    assert convert_value_to_fielddata("boolean", "123") is True
    assert convert_value_to_fielddata("code", "123") == "123"
    assert convert_value_to_fielddata("barcode", "123") == "123"
    assert convert_value_to_fielddata("class", '{"abc": "123"}') == {"abc": "123"}
    assert convert_value_to_fielddata(
        "classlist", '[{"abc": "123"},{"def": "456"}]'
    ) == [{"abc": "123"}, {"def": "456"}]
    assert convert_value_to_fielddata("image", "<gid-123>") == "<gid-123>"
    assert convert_value_to_fielddata("imagelist", "<gid-123>\n<gid-456>") == [
        "<gid-123>",
        "<gid-456>",
    ]
    assert convert_value_to_fielddata("file", "<gid-123>") == "<gid-123>"
    assert convert_value_to_fielddata("filelist", "<gid-123>\n<gid-456>") == [
        "<gid-123>",
        "<gid-456>",
    ]
    assert convert_value_to_fielddata("record", "<gid-123>") == "<gid-123>"
    assert convert_value_to_fielddata("recordlist", "<gid-123>\n<gid-456>") == [
        "<gid-123>",
        "<gid-456>",
    ]
    assert convert_value_to_fielddata("fieldpicker", "<gid-123>") == "<gid-123>"


def test_convert_value_to_fielddata_errors():
    with pytest.raises(Exception):
        convert_value_to_fielddata("class", "abc")
    with pytest.raises(Exception):
        convert_value_to_fielddata("classlist", "abc")


def test_convert_fielddata_to_value():
    assert convert_fielddata_to_value("text", "123") == "123"
    assert convert_fielddata_to_value("textline", "123") == "123"
    assert convert_fielddata_to_value("textlist", ["123", "456"]) == "123\n456"
    assert convert_fielddata_to_value("number", 123) == 123
    assert convert_fielddata_to_value("decimal", 123) == 123
    assert convert_fielddata_to_value("decimal", 123.45) == 123.45
    assert convert_fielddata_to_value("boolean", True) == "yes"
    assert convert_fielddata_to_value("code", "123") == "123"
    assert convert_fielddata_to_value("barcode", "123") == "123"
    assert convert_fielddata_to_value("class", {"abc": "123"}) == '{\n  "abc": "123"\n}'
    assert (
        convert_fielddata_to_value("classlist", [{"abc": "123"}, {"def": "456"}])
        == '[\n  {\n    "abc": "123"\n  },  {\n    "def": "456"\n  }\n]'
    )
    assert convert_fielddata_to_value("image", "<gid-123>") == "<gid-123>"
    assert (
        convert_fielddata_to_value("imagelist", ["<gid-123>", "<gid-456>"])
        == "<gid-123>\n<gid-456>"
    )
    assert convert_fielddata_to_value("file", "<gid-123>") == "<gid-123>"
    assert (
        convert_fielddata_to_value("filelist", ["<gid-123>", "<gid-456>"])
        == "<gid-123>\n<gid-456>"
    )
    assert convert_fielddata_to_value("record", "<gid-123>") == "<gid-123>"
    assert (
        convert_fielddata_to_value("recordlist", ["<gid-123>", "<gid-456>"])
        == "<gid-123>\n<gid-456>"
    )
    assert convert_fielddata_to_value("fieldpicker", "<gid-123>") == "<gid-123>"


def test_diff_record_fields_data(unicat):
    record = unicat.get_root_record()
    localizedfielddata = {
        "en": {"field-1-name": "Field 1 value 0"},
        "nl": {"field-1-name": "Veld 1 waarde 0"},
    }
    diff = diff_record_fields_data(unicat, record, localizedfielddata)
    assert not len(diff)
    localizedfielddata = {
        "en": {"field-1-name": "Field 1 value CHANGED"},
        "nl": {"field-1-name": "Veld 1 waarde 0"},
    }
    diff = diff_record_fields_data(unicat, record, localizedfielddata)
    assert len(diff) == 1
    assert "en" in diff
    assert "nl" not in diff
    localizedfielddata = {
        "en": {"field-1-name": "Field 1 value CHANGED"},
        "nl": {"field-1-name": "Veld 1 waarde AANGEPAST"},
    }
    diff = diff_record_fields_data(unicat, record, localizedfielddata)
    assert len(diff) == 2
    assert "en" in diff
    assert "nl" in diff


def test_merge_dicts():
    a = {"a": 1, "c": 99}
    x = merge_dicts(a, {"b": 2, "c": 3})
    assert x["a"] == a["a"] == 1
    assert x["b"] == a["b"] == 2
    assert x["c"] == a["c"] == 3
    a = {"a": 1, "c": 99}
    x = merge_dicts(dict(a), {"b": 2, "c": 3})
    assert x["a"] == a["a"] == 1
    assert x["b"] == 2
    assert x["c"] == 3
    assert a["c"] == 99


def check_hash(hash):
    if len(hash) != 8:
        return False
    for char in hash:
        if char not in "0123456789abcdef":
            return False
    return True


def test_check_hash():
    assert check_hash("1234abcd")
    assert not check_hash("1234ABCD")
    assert not check_hash("1234GHIJ")
    assert not check_hash("1234abc")
    assert not check_hash("1234abcde")


def test_hash_text():
    assert check_hash(hash_text("abcdef"))
    assert check_hash(hash_text("🧐🥸"))


def test_hash_data():
    assert check_hash(hash_data([1, 2, 3]))
    assert check_hash(hash_data({"a": "b", "c": [1, 2, 3]}))


def test_metadata(unicat):
    raw_metadata = {
        "a.b": {
            "type": "fieldpicker",
            "is_localized": False,
            "value": "0c9ca0a8-fa1b-4573-ac98-81b583b7b07c",
        },
        "a.c": {
            "type": "image",
            "is_localized": True,
            "value": {"en": "a0a80c9c-fa1b-4573-ac98-b7b07c81b583", "nl": None},
        },
    }
    metadata = {}
    for name, metadata_field in raw_metadata.items():
        metadata[name] = UnicatMetadataField(unicat, name, metadata_field)

    serialized_raw_metadata = serialize_metadata(raw_metadata)
    serialized_metadata = serialize_metadata(metadata)
    assert serialized_raw_metadata == serialized_metadata
