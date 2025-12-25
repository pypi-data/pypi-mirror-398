import pytest

from unicat import UnicatError
from unicat.utils import DuckObject

# we test most methods with unicaterror, but that will test the code-paths for
# arguments &c.


def test_mutate(unicat):
    assert hasattr(unicat, "mutate")


def test_mutate_project_settings(unicaterror):
    with pytest.raises(UnicatError):
        unicaterror.mutate.add_language("it")
    with pytest.raises(UnicatError):
        unicaterror.mutate.remove_language("it")
    with pytest.raises(UnicatError):
        unicaterror.mutate.create_channel("New Channel Name")
    with pytest.raises(UnicatError):
        unicaterror.mutate.delete_channel(unicaterror.project.default_channel)
    with pytest.raises(UnicatError):
        unicaterror.mutate.create_ordering("New Ordering Name")
    with pytest.raises(UnicatError):
        unicaterror.mutate.delete_ordering(unicaterror.project.default_ordering)
    with pytest.raises(UnicatError):
        unicaterror.mutate.create_fieldlist("New Fieldlist Name")
    with pytest.raises(UnicatError):
        unicaterror.mutate.delete_fieldlist(unicaterror.project.default_fieldlist)


def test_mutate_definitions(unicaterror):
    language = unicaterror.project.default_language
    fieldlist = unicaterror.project.default_fieldlist
    definition = unicaterror.get_definition("<definition-1>")
    duckdefinition = DuckObject(gid="<definition-duck>")
    class_ = unicaterror.get_class("<class-1>")
    field = unicaterror.get_field("<field-1>")
    with pytest.raises(UnicatError):
        unicaterror.mutate.create_definition(
            name="new",
            label={language: "New"},
            classes=[class_],
            fields=[field],
            titlefield=field,
            childdefinitions=[],
            metadata={},
        )
    with pytest.raises(UnicatError):
        unicaterror.mutate.create_definition(
            other="layout - know what you're doing!",
        )
    with pytest.raises(UnicatError):
        unicaterror.mutate.modify_definition(
            definition,
            name="new",
            label={language: "New"},
            classes=[class_],
            fields=[field],
            titlefield=field,
            childdefinitions=[],
            metadata={},
        )
    with pytest.raises(UnicatError):
        unicaterror.mutate.modify_definition(
            definition,
            other="layout - know what you're doing!",
        )
    with pytest.raises(UnicatError):
        # also - know what you're doing!
        unicaterror.mutate.modify_definition_modify_layout(
            definition,
            name="layout",
            root="<gid>",
            components={"<gid>": {"type": "vertical", "content": []}},
        )
    with pytest.raises(UnicatError):
        unicaterror.mutate.modify_definition_add_class(definition, class_)
    with pytest.raises(UnicatError):
        unicaterror.mutate.modify_definition_remove_class(definition, class_)
    with pytest.raises(UnicatError):
        unicaterror.mutate.modify_definition_add_field(definition, field)
    with pytest.raises(UnicatError):
        unicaterror.mutate.modify_definition_remove_field(definition, field)
    with pytest.raises(UnicatError):
        unicaterror.mutate.modify_definition_fieldlist_add_field(
            definition, fieldlist, field
        )
    with pytest.raises(UnicatError):
        unicaterror.mutate.modify_definition_fieldlist_remove_field(
            definition, fieldlist, field
        )
    with pytest.raises(UnicatError):
        unicaterror.mutate.modify_definition_add_childdefinition(
            definition, childdefinition=duckdefinition
        )
    with pytest.raises(UnicatError):
        unicaterror.mutate.modify_definition_remove_childdefinition(
            definition, childdefinition=duckdefinition
        )
    with pytest.raises(UnicatError):
        unicaterror.mutate.modify_definition_set_metadata(duckdefinition, "dotted.name")
    with pytest.raises(UnicatError):
        unicaterror.mutate.modify_definition_clear_metadata(
            duckdefinition, "dotted.name"
        )
    with pytest.raises(UnicatError):
        unicaterror.mutate.commit_definition(duckdefinition)
    with pytest.raises(UnicatError):
        unicaterror.mutate.save_as_new_definition(duckdefinition)
    with pytest.raises(UnicatError):
        unicaterror.mutate.delete_definition(definition)


def test_mutate_classes(unicaterror):
    language = unicaterror.project.default_language
    class_ = unicaterror.get_class("<class-1>")
    duckclass = DuckObject(gid="<class-duck>")
    field = unicaterror.get_field("<field-1>")
    with pytest.raises(UnicatError):
        unicaterror.mutate.create_class(
            name="new", label={language: "New"}, fields=[field], metadata={}
        )
    with pytest.raises(UnicatError):
        unicaterror.mutate.create_class(
            other="layout - know what you're doing!",
        )
    with pytest.raises(UnicatError):
        unicaterror.mutate.modify_class(
            class_, name="new", label={language: "New"}, fields=[field], metadata={}
        )
    with pytest.raises(UnicatError):
        unicaterror.mutate.modify_class(
            class_,
            other="layout - know what you're doing!",
        )
    with pytest.raises(UnicatError):
        # also - know what you're doing!
        unicaterror.mutate.modify_class_modify_layout(
            class_,
            name="layout",
            root="<gid>",
            components={"<gid>": {"type": "vertical", "content": []}},
        )
    with pytest.raises(UnicatError):
        unicaterror.mutate.modify_class_add_field(class_, field)
    with pytest.raises(UnicatError):
        unicaterror.mutate.modify_class_remove_field(class_, field)
    with pytest.raises(UnicatError):
        unicaterror.mutate.modify_class_set_metadata(duckclass, "dotted.name")
    with pytest.raises(UnicatError):
        unicaterror.mutate.modify_class_clear_metadata(duckclass, "dotted.name")
    with pytest.raises(UnicatError):
        unicaterror.mutate.commit_class(duckclass)
    with pytest.raises(UnicatError):
        unicaterror.mutate.save_as_new_class(duckclass)
    with pytest.raises(UnicatError):
        unicaterror.mutate.delete_class(class_)


def test_mutate_fields(unicaterror):
    language = unicaterror.project.default_language
    field = unicaterror.get_field("<field-1>")
    duckfield = DuckObject(gid="<field-duck>")
    with pytest.raises(UnicatError):
        unicaterror.mutate.create_field(
            name="new",
            type="text",
            is_localized=True,
            is_required=False,
            label={language: "New"},
            unit="mm²",
            initial={},
            options={},
            metadata={},
        )
    with pytest.raises(UnicatError):
        unicaterror.mutate.modify_field(
            field,
            name="new",
            type="text",
            is_localized=True,
            is_required=False,
            label={language: "New"},
            unit="mm²",
            initial={},
            options={},
            metadata={},
        )
    with pytest.raises(UnicatError):
        unicaterror.mutate.modify_field_set_metadata(duckfield, "dotted.name")
    with pytest.raises(UnicatError):
        unicaterror.mutate.modify_field_clear_metadata(duckfield, "dotted.name")
    with pytest.raises(UnicatError):
        unicaterror.mutate.commit_field(duckfield)
    with pytest.raises(UnicatError):
        unicaterror.mutate.save_as_new_field(duckfield)
    with pytest.raises(UnicatError):
        unicaterror.mutate.delete_field(field)


def test_mutate_records(unicaterror):
    language = unicaterror.project.default_language
    channel = unicaterror.project.default_channel
    ordering = unicaterror.project.default_ordering
    fieldlist = unicaterror.project.default_fieldlist
    record = unicaterror.get_record("<record-1>")
    parentrecord = unicaterror.get_record("<record-0>")
    definition = unicaterror.get_definition("<definition-1>")
    class_ = unicaterror.get_class("<class-1>")
    field = unicaterror.get_field("<field-1>")
    with pytest.raises(UnicatError):
        unicaterror.mutate.create_record(parentrecord, ordering=ordering)
    with pytest.raises(UnicatError):
        unicaterror.mutate.set_record_definition(record, definition)
    with pytest.raises(UnicatError):
        unicaterror.mutate.extend_record_definition_add_class(record, class_)
    with pytest.raises(UnicatError):
        unicaterror.mutate.extend_record_definition_add_field(record, field)
    with pytest.raises(UnicatError):
        unicaterror.mutate.extend_record_definition_add_fieldlist_field(
            record, fieldlist, field
        )
    with pytest.raises(UnicatError):
        unicaterror.mutate.extend_record_definition_remove_class(record, class_)
    with pytest.raises(UnicatError):
        unicaterror.mutate.extend_record_definition_remove_field(record, field)
    with pytest.raises(UnicatError):
        unicaterror.mutate.extend_record_definition_remove_fieldlist_field(
            record, fieldlist, field
        )
    with pytest.raises(UnicatError):
        unicaterror.mutate.revert_extended_record_definition(record)
    with pytest.raises(UnicatError):
        unicaterror.mutate.copy_record_definition_to_siblings(record)
    with pytest.raises(UnicatError):
        unicaterror.mutate.update_record(
            record, localizedfielddata={language: {"field-1-name": "value"}}
        )
    with pytest.raises(UnicatError):
        unicaterror.mutate.update_record(
            record, localizedfielddata={language: {"field-3-name/key": "g"}}
        )
    with pytest.raises(UnicatError):
        unicaterror.mutate.set_record_channels(record, channels=[channel], enabled=True)
    with pytest.raises(UnicatError):
        unicaterror.mutate.copy_record_channels_from_parent(record, channels=[channel])
    with pytest.raises(UnicatError):
        unicaterror.mutate.copy_record_channels_down(record, channels=[channel])
    with pytest.raises(UnicatError):
        unicaterror.mutate.copy_record_channels_up(record, channels=[channel])
    with pytest.raises(UnicatError):
        unicaterror.mutate.set_record_orderings(record, orderings={ordering: 123})
    with pytest.raises(UnicatError):
        unicaterror.mutate.link_record(parentrecord, record, ordering=ordering)
    with pytest.raises(UnicatError):
        unicaterror.mutate.delete_record(record)
    with pytest.raises(UnicatError):
        unicaterror.mutate.undelete_record(record)
    with pytest.raises(UnicatError):
        unicaterror.mutate.permanent_delete_record(record)


def test_mutate_assets(unicaterror):
    language = unicaterror.project.default_language
    asset = unicaterror.get_asset("<asset-1>")
    folderasset = unicaterror.get_asset("<asset-0>")
    localfilepath = "/tmp/localfile.ext"
    with pytest.raises(UnicatError):
        unicaterror.mutate.upload_asset(localfilepath, folderasset)
    with pytest.raises(UnicatError):
        unicaterror.mutate.upload_update_asset(localfilepath, asset)
    with pytest.raises(UnicatError):
        unicaterror.mutate.create_asset(folderasset, name="new folder")
    with pytest.raises(UnicatError):
        unicaterror.mutate.update_asset(
            asset,
            name="new",
            title={language: "New"},
            description={language: "New new new"},
        )
    with pytest.raises(UnicatError):
        unicaterror.mutate.update_asset(
            asset,
            other="transforms - know what you're doing!",
        )
    with pytest.raises(UnicatError):
        unicaterror.mutate.delete_asset(asset)
    with pytest.raises(UnicatError):
        unicaterror.mutate.undelete_asset(asset)
    with pytest.raises(UnicatError):
        unicaterror.mutate.permanent_delete_asset(asset)


def test_mutate_queries(unicaterror):
    query = unicaterror.get_query("<query-1>")
    with pytest.raises(UnicatError):
        unicaterror.mutate.create_query(
            type="record",
            name="new",
            q="",
            filter=["and", "", [["validation", "not_translated"]]],
        )
    with pytest.raises(UnicatError):
        unicaterror.mutate.update_query(
            query,
            name="updated",
            q="",
            filter=["and", "", [["validation", "not_translated"]]],
        )
    with pytest.raises(UnicatError):
        unicaterror.mutate.delete_query(query)


def test_mutate_modules(unicaterror):
    module = unicaterror.get_module("Module 1")
    with pytest.raises(UnicatError):
        unicaterror.mutate.register_module("Module Error Result", "3.2.1")
    with pytest.raises(UnicatError):
        unicaterror.mutate.unregister_module(module)
    with pytest.raises(UnicatError):
        unicaterror.mutate.set_module_key(module, key="key", value="value")
    with pytest.raises(UnicatError):
        unicaterror.mutate.set_module_keys(module, keyvalues={"key": "value"})
    with pytest.raises(UnicatError):
        unicaterror.mutate.clear_module_key(module, key="key")
    with pytest.raises(UnicatError):
        unicaterror.mutate.clear_module_keys(module, keys=["key"])
    with pytest.raises(UnicatError):
        unicaterror.mutate.publish_module_action(
            module, action="action", configuration={}
        )
    with pytest.raises(UnicatError):
        unicaterror.mutate.unpublish_module_action(module, action="action")
    with pytest.raises(UnicatError):
        unicaterror.mutate.add_module_log(
            module, "0.0.1", action="action", configuration={}, command="test"
        )


def test_backups(unicaterror):
    backup = unicaterror.project.get_backup(2)
    with pytest.raises(UnicatError):
        unicaterror.mutate.create_backup(created_by="unicat test", name="new")
    with pytest.raises(UnicatError):
        unicaterror.mutate.update_backup(backup, "updated")
    with pytest.raises(UnicatError):
        unicaterror.mutate.delete_backup(backup)
    with pytest.raises(UnicatError):
        unicaterror.mutate.delete_backups(unicaterror.project.backups[0:2])
