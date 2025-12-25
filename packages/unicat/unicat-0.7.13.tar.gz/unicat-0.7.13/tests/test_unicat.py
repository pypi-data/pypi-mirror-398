import pytest

from unicat import UnicatError, UnicatTransform


def test_connect(unicat):
    assert unicat.connect()


def test_connect_error(unicaterror):
    assert not unicaterror.connect()


def test_sync(unicat):
    assert unicat.sync()


def test_sync_error(unicaterror):
    with pytest.raises(UnicatError):
        unicaterror.sync()


def test_project_user_members(unicat):
    assert unicat.project.gid == "<project-1>"
    assert unicat.project.name == "Project the First"
    assert unicat.project.owner.name == "User the First"
    assert unicat.project.icon == "project-1-icon.jpg"
    assert unicat.project.status == "active"
    assert unicat.project.languages == ["en", "nl"]
    assert unicat.project.default_language == "en"
    assert unicat.project.channels["Channel the Second"] == "<channel-2>"
    assert unicat.project.default_channel == "<channel-1>"
    assert unicat.project.channel_name("<channel-1>") == "Channel the First"
    assert unicat.project.orderings["Ordering the First"] == "<ordering-1>"
    assert unicat.project.default_ordering == "<ordering-1>"
    assert unicat.project.ordering_name("<ordering-1>") == "Ordering the First"
    assert unicat.project.fieldlists["Fieldlist the First"] == "<fieldlist-1>"
    assert unicat.project.default_fieldlist == "<fieldlist-1>"
    assert unicat.project.fieldlist_name("<fieldlist-1>") == "Fieldlist the First"
    assert unicat.project.members[0].project.name == "Project the First"
    assert unicat.project.members[0].user.name == "User the First"
    owner = unicat.project.owner
    assert owner.gid == "<user-1>"
    assert owner.username == "user-1"
    assert owner.name == "User the First"
    assert owner.avatar == "user-1-avatar.png"
    member = unicat.project.members[0]
    assert member.key == "<project-1>/<user-1>"
    assert member.project.name == "Project the First"
    assert member.user.name == "User the First"
    assert member.status == "active"
    assert member.roles == [
        "owner",
    ]
    assert hasattr(member, "options")


def test_project_backups(unicat):
    assert unicat.project.get_backup(1).name == "Backup 1"
    assert unicat.project.get_backup(3).name == "Backup 3"
    assert len(unicat.project.backups) == 3
    assert unicat.project.backups[0].name == "Backup 3"
    assert unicat.project.backups[1].name == "Backup 2"
    assert unicat.project.backups[2].name == "Backup 1"
    assert unicat.project.get_backup(123) is None


def test_definition(unicat):
    language = unicat.project.default_language
    fieldlist = unicat.project.default_fieldlist
    definition = unicat.get_definition("<definition-1>")
    assert definition.gid == "<definition-1>"
    assert definition.original is None
    assert definition.name == "definition-1-name"
    assert definition.label[language] == "Definition 1"
    assert definition.classes[0].gid == "<class-1>"
    assert definition.classes_as_gids[0] == "<class-1>"
    assert definition.fields[0].gid == "<field-1>"
    assert definition.fields_as_gids[0] == "<field-1>"
    assert definition.titlefield.gid == "<field-1>"
    assert definition.fieldlists[fieldlist][0].gid == "<field-1>"
    assert definition.layout.gid == "<layout-1>"
    assert len(definition.childdefinitions) == 0
    assert definition.is_base is False
    assert definition.is_new is False
    assert definition.is_extended is False
    assert definition.is_working_copy is False
    assert definition.is_committed is True
    assert set(field.gid for field in definition.all_fields) == set(
        ["<field-1>", "<field-2>", "<field-3>", "<field-4>", "<field-5>", "<field-6>"]
    )
    assert set(class_.gid for class_ in definition.base_classes) == set(["<class-1>"])
    assert set(field.gid for field in definition.base_fields) == set(
        ["<field-1>", "<field-2>", "<field-3>", "<field-4>", "<field-5>", "<field-6>"]
    )
    assert set(field.gid for field in definition.all_base_fields) == set(
        ["<field-1>", "<field-2>", "<field-3>", "<field-4>", "<field-5>", "<field-6>"]
    )
    assert definition.extended_classes == []
    assert definition.extended_fields == []
    assert definition.all_extended_fields == []
    assert definition.metadata == {}


def test_class(unicat):
    language = unicat.project.default_language
    class_ = unicat.get_class("<class-1>")
    assert class_.gid == "<class-1>"
    assert class_.original is None
    assert class_.name == "class-1-name"
    assert class_.label[language] == "Class 1"
    assert class_.fields[0].gid == "<field-1>"
    assert class_.fields_as_gids[0] == "<field-1>"
    assert class_.layout.gid == "<layout-2>"
    assert class_.is_new is False
    assert class_.is_working_copy is False
    assert class_.is_committed is True
    assert class_.metadata == {}


def test_field(unicat):
    language = unicat.project.default_language
    field = unicat.get_field("<field-1>")
    assert field.gid == "<field-1>"
    assert field.original is None
    assert field.name == "field-1-name"
    assert field.type == "text"
    assert field.class_ is None
    assert field.options == {}
    assert field.is_localized is True
    assert field.is_required is False
    assert field.label[language] == "Field 1"
    assert field.initial[language] == ""
    assert field.unit == "m²"
    assert field.title[language] == "Field 1 [m²]"
    assert field.is_new is False
    assert field.is_working_copy is False
    assert field.is_committed is True
    assert field.metadata == {}
    field2 = unicat.get_field("<field-2>")  # no unit
    assert field2.title[language] == "Field 2"
    field3 = unicat.get_field("<field-3>")
    assert field3.title[language] == "Field 3"
    assert "values" in field3.options and field3.options["values"]
    assert "key" in field3.initial
    field4 = unicat.get_field("<field-4>")
    assert field4.title[language] == "Field 4"
    assert "values" in field4.options and field4.options["values"]
    assert "key" in field4.initial


def test_layout(unicat):
    layout = unicat.get_definition("<definition-1>").layout
    assert layout.gid == "<layout-1>"
    assert layout.original is None
    assert layout.name == "layout-1-name"
    assert layout.root == "<component-1>"
    assert layout.components[layout.root]["type"] == "vertical"
    assert layout.is_new is False
    assert layout.is_working_copy is False


def test_query(unicat):
    query = unicat.get_query("<query-1>")
    assert query.gid == "<query-1>"
    assert query.type == "record"
    assert query.name == "query-1-record-name"
    assert query.q == ""
    assert query.filter == ["and", "", [["validation", "not_translated"]]]


def test_asset_folder(unicat):
    language = unicat.project.default_language
    transform = UnicatTransform(resize="fill", width=400, height=300)
    asset = unicat.get_asset("<asset-0>")
    assert asset.gid == "<asset-0>"
    assert asset.pathname == "/"
    assert asset.path == "/"
    assert asset.name == ""
    assert asset.is_file is False
    assert asset.type is None
    assert asset.childcount == 1
    assert asset.status == "published"
    assert asset.is_deleted is False
    assert "filecount" in asset.info
    assert asset.transforms is None
    assert asset.default_transform is None
    assert asset.title[language] == "Asset the Root"
    assert asset.description[language] == ""
    assert asset.created_on == pytest.approx(1610635126.04762)
    assert asset.updated_on == pytest.approx(1610635126.04762)
    assert asset.publish() is None
    assert asset.publish_transformed(transform) is None
    assert asset.download() is None
    assert asset.download_transformed(transform) is None


def test_asset_file(unicat):
    language = unicat.project.default_language
    transform = UnicatTransform(resize="fill", width=400, height=300)
    asset = unicat.get_asset("<asset-1>")
    assert asset.gid == "<asset-1>"
    assert asset.pathname == "/asset-1-name.svg"
    assert asset.path == "/"
    assert asset.name == "asset-1-name.svg"
    assert asset.is_file is True
    assert asset.type == "svg"
    assert asset.childcount == 0
    assert asset.status == "published"
    assert asset.is_deleted is False
    assert "width" in asset.info
    assert "_main_" in asset.transforms
    assert "hotspot" in asset.default_transform
    assert asset.title[language] == "A generic image"
    assert (
        asset.description[language]
        == "Image - a line drawing of a frame containing mountains and the sun."
    )
    assert asset.created_on == pytest.approx(1610635123.351925)
    assert asset.updated_on == pytest.approx(1610635123.351925)
    assert asset.publish() == "mocks://unicat.app/p/src/any-filename.ext"
    assert (
        asset.publish_transformed(transform)
        == "mocks://unicat.app/p/src/any-filename.ext"
    )
    assert asset.download() == "/tmp/unicat/any-filename.ext"
    assert asset.download_transformed(transform) == "/tmp/unicat/any-filename.ext"


def test_record(unicat):
    language = unicat.project.default_language
    ordering = unicat.project.default_ordering
    record = unicat.get_record("<record-1>")
    assert record.gid == "<record-1>"
    assert record.canonical == "<record-1>"  # should this be type UnicatRecord?
    assert record.parent == "<record-0>"  # should this be type UnicatRecord?
    assert record.backlinks == []  # should this be type list[UnicatRecord]?
    assert record.is_link is False
    assert record.is_deleted is False
    assert record.treelevel == 2
    assert record.path == ["<record-1>", "<record-0>"]
    assert record.title[language] == "Record the First"
    assert record.channels == ["__all__", "<channel-1>"]
    assert record.orderings[ordering] == 1
    assert record.childcount == 0
    assert record.definition.gid == "<definition-1>"
    assert record.created_on == pytest.approx(1610635126.14762)
    assert record.updated_on == pytest.approx(1610635126.14762)
    assert isinstance(record.fields[language], dict)


def test_record_fields(unicat):
    language = unicat.project.default_language
    fields = unicat.get_record("<record-1>").fields[language]
    assert len(fields) == 6
    field1 = fields["field-1-name"]
    assert field1.key is None
    assert field1.value == "Field 1 value 1"
    assert field1.field.gid == "<field-1>"
    field3 = fields["field-3-name"]
    assert field3.key == "r"
    assert field3.value == "Red"
    assert field3.field.gid == "<field-3>"
    with pytest.raises(KeyError):
        fields["field-3-name/key"]
    field4 = fields["field-4-name"]
    assert field4.key == ["r"]
    assert field4.value == ["Red"]
    assert field4.field.gid == "<field-4>"
    with pytest.raises(KeyError):
        fields["field-4-name/key"]
    field5 = fields["field-5-name"]
    assert field5.field.gid == "<field-5>"
    assert field5["field-3-name"].key == "r"
    assert field5["field-3-name"].value == "Red"
    assert field5["field-4-name"].key == ["r"]
    assert field5["field-4-name"].value == ["Red"]
    with pytest.raises(KeyError):
        field5["field-4-name/key"]
    field6 = fields["field-6-name"]
    assert field6.field.gid == "<field-6>"
    assert field6[0]["field-3-name"].key == "r"
    assert field6[0]["field-3-name"].value == "Red"
    assert field6[0]["field-4-name"].key == ["r"]
    assert field6[0]["field-4-name"].value == ["Red"]
    with pytest.raises(KeyError):
        field6[0]["field-4-name/key"]


def test_methods_reading(unicat):
    assert unicat.get_record("<record-1>").gid == "<record-1>"
    assert unicat.get_records(["<record-1>"])[0].gid == "<record-1>"
    assert unicat.get_root_record().gid == "<record-0>"
    assert unicat.get_asset("<asset-1>").gid == "<asset-1>"
    assert unicat.get_asset_by_pathname("/asset-1-name.svg").gid == "<asset-1>"
    assert unicat.get_assets(["<asset-1>"])[0].gid == "<asset-1>"
    assert (
        unicat.get_assets_by_pathname(["/asset-1-name.svg"])["/asset-1-name.svg"].gid
        == "<asset-1>"
    )
    assert unicat.get_root_asset().gid == "<asset-0>"
    assert unicat.get_definition("<definition-1>").gid == "<definition-1>"
    assert unicat.get_definitions(["<definition-1>"])[0].gid == "<definition-1>"
    assert unicat.get_definition_by_name("definition-1-name").gid == "<definition-1>"
    assert (
        unicat.get_definitions_by_name(["definition-1-name"])["definition-1-name"].gid
        == "<definition-1>"
    )
    assert unicat.get_class("<class-1>").gid == "<class-1>"
    assert unicat.get_classes(["<class-1>"])[0].gid == "<class-1>"
    assert unicat.get_class_by_name("class-1-name").gid == "<class-1>"
    assert (
        unicat.get_classes_by_name(["class-1-name"])["class-1-name"].gid == "<class-1>"
    )
    assert unicat.get_field("<field-1>").gid == "<field-1>"
    assert unicat.get_fields(["<field-1>"])[0].gid == "<field-1>"
    assert unicat.get_field_by_name("field-1-name").gid == "<field-1>"
    assert (
        unicat.get_fields_by_name(["field-1-name"])["field-1-name"].gid == "<field-1>"
    )
    assert unicat.get_query("<query-1>").gid == "<query-1>"
    assert unicat.get_queries(["<query-1>"])[0].gid == "<query-1>"
    assert unicat.get_record_query_by_name("query-1-record-name").gid == "<query-1>"
    assert (
        unicat.get_record_queries_by_name(["query-1-record-name"])[
            "query-1-record-name"
        ].gid
        == "<query-1>"
    )
    assert unicat.get_asset_query_by_name("query-2-asset-name").gid == "<query-2>"
    assert (
        unicat.get_asset_queries_by_name(["query-2-asset-name"])[
            "query-2-asset-name"
        ].gid
        == "<query-2>"
    )
    assert unicat.get_schema_query_by_name("query-3-schema-name").gid == "<query-3>"
    assert (
        unicat.get_schema_queries_by_name(["query-3-schema-name"])[
            "query-3-schema-name"
        ].gid
        == "<query-3>"
    )
    assert len(unicat.get_all_module_names()) == 3
    assert unicat.get_module("Module 1").name == "Module 1"
    assert unicat.get_modules(["Module 2", "Module 1"])[0].name == "Module 2"


def test_methods_reading_nonexisting(unicat):
    with pytest.raises(UnicatError):
        unicat.get_record("<record-999>")
    assert len(unicat.get_records(["<record-999>"])) == 0
    with pytest.raises(UnicatError):
        unicat.get_asset("<asset-999>")
    assert len(unicat.get_assets(["<asset-999>"])) == 0
    assert unicat.get_definition("<definition-999>") is None
    assert len(unicat.get_definitions(["<definition-999>"])) == 0
    assert unicat.get_definition_by_name("definition-999-name") is None
    assert (
        unicat.get_definitions_by_name(["definition-999-name"])["definition-999-name"]
        is None
    )
    assert unicat.get_class("<class-999>") is None
    assert len(unicat.get_classes(["<class-999>"])) == 0
    assert unicat.get_class_by_name("class-999-name") is None
    assert unicat.get_classes_by_name(["class-999-name"])["class-999-name"] is None
    assert unicat.get_field("<field-999>") is None
    assert len(unicat.get_fields(["<field-999>"])) == 0
    assert unicat.get_field_by_name("field-999-name") is None
    assert unicat.get_fields_by_name(["field-999-name"])["field-999-name"] is None
    assert unicat.get_query("<query-999>") is None
    assert len(unicat.get_queries(["<query-999>"])) == 0
    assert unicat.get_record_query_by_name("query-999-record-name") is None
    assert (
        unicat.get_record_queries_by_name(["query-999-record-name"])[
            "query-999-record-name"
        ]
        is None
    )
    assert unicat.get_asset_query_by_name("query-999-asset-name") is None
    assert (
        unicat.get_asset_queries_by_name(["query-999-asset-name"])[
            "query-999-asset-name"
        ]
        is None
    )
    assert unicat.get_schema_query_by_name("query-999-schema-name") is None
    assert (
        unicat.get_schema_queries_by_name(["query-999-schema-name"])[
            "query-999-schema-name"
        ]
        is None
    )
    with pytest.raises(UnicatError):
        unicat.get_module("Module 999")
    assert len(unicat.get_modules(["Module 999"])) == 0


def test_methods_reading_error(unicaterror):
    with pytest.raises(UnicatError):
        unicaterror.get_record("<record-999>")
    with pytest.raises(UnicatError):
        unicaterror.get_records(["<record-999>"])
    with pytest.raises(UnicatError):
        unicaterror.get_root_record()
    with pytest.raises(UnicatError):
        unicaterror.get_asset("<asset-999>")
    with pytest.raises(UnicatError):
        unicaterror.get_asset_by_pathname("asset-999-pathname")
    with pytest.raises(UnicatError):
        unicaterror.get_assets(["<asset-999>"])
    with pytest.raises(UnicatError):
        unicaterror.get_root_asset()
    with pytest.raises(UnicatError):
        unicaterror.get_all_module_names()
    with pytest.raises(UnicatError):
        unicaterror.get_module("Module 999")
    with pytest.raises(UnicatError):
        unicaterror.get_modules(["Module 999"])


def test_methods_traversing(unicat):
    record = unicat.get_record("<record-1>")
    asset = unicat.get_asset("<asset-1>")
    language = unicat.project.default_language
    record_query = unicat.get_query("<query-1>")
    asset_query = unicat.get_query("<query-2>")
    schema_query = unicat.get_query("<query-3>")
    assert hasattr(unicat.walk_record_children(record), "__iter__")
    assert hasattr(unicat.walk_record_tree(), "__iter__")
    assert hasattr(unicat.walk_record_query(language, record_query), "__iter__")
    assert hasattr(unicat.walk_asset_children(asset), "__iter__")
    assert hasattr(unicat.walk_asset_tree(), "__iter__")
    assert hasattr(unicat.walk_asset_query(language, asset_query), "__iter__")
    assert hasattr(unicat.walk_definitions(), "__iter__")
    assert hasattr(unicat.walk_classes(), "__iter__")
    assert hasattr(unicat.walk_fields(), "__iter__")
    assert hasattr(unicat.walk_schema_query(language, schema_query), "__iter__")
    assert hasattr(unicat.walk_queries(), "__iter__")
    assert hasattr(unicat.walk_modules(), "__iter__")
