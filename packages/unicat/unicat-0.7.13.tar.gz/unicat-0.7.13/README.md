# Unicat client library

Unicat is a Product Information Management SaaS.

This library is still a work in progress, not all Unicat API options are covered yet.

Documentation still needs a bit of work too.


First, connect to Unicat (https://unicat.app):

```
import sys
from unicat import Unicat
from .env import server, project_gid, api_key, local_folder

# please use the keyring module in .env to store/retrieve the api_key

unicat = Unicat(server, project_gid, api_key, local_folder)
if not unicat.connect():
  print("Invalid connection settings")
  sys.exit(1)
```

Download all assets for the project (you can find them in the local_folder):

```
for asset in unicat.walk_asset_tree():
  if asset.is_file:
    asset.download()
```

Or, write an XML product feed:

```
with open("product-feed.xml", "w", encoding="utf-8") as f:
  f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
  f.write('<products>\n')

  for record in unicat.walk_record_tree():
    if record.definition.name != "article":
      continue

    fields = record.fields["nl"]

    artnr = fields["artnr"].value
    price = fields["price"].value
    stock = fields["stock"].value

    f.write(f'  <product artnr="{artnr}" price="{price:%0.02f}" stock="{stock}"/>\n')
  f.write('</products>\n')
```

There's also unicat.mutate, with options to update the Unicat project server-side, like unicat.mutate.create_record, unicat.mutate.modify_field and many more.


## The `unicat` package

The Unicat package is split into connection, reading/traversing, and mutating. All mutating methods below are available on the `unicat.mutate` property. All methods raise a UnicatError on error.


### Connection methods

```python
unicat.connect() -> bool
unicat.sync() -> True
```

### Reading methods

```python
unicat.get_record(gid: str, *, force: bool) -> UnicatRecord | None
unicat.get_records(gids: list[str], *, force: bool) -> list[UnicatRecord]
unicat.get_root_record() -> UnicatRecord
unicat.get_asset(gid: str, *, force: bool) -> UnicatAsset | None
unicat.get_asset_by_pathname(pathname: str, *, force: bool) -> UnicatAsset | None
unicat.get_assets(gids: list[str], *, force: bool) -> list[UnicatAsset]
unicat.get_assets_by_pathname(pathnames: list[str], *, force: bool) -> dict[str, UnicatAsset]
unicat.get_root_asset() -> UnicatAsset
unicat.get_definition(gid: str) -> UnicatDefinition | None
unicat.get_definitions(gids: list[str]) -> list[UnicatDefinition]
unicat.get_definition_by_name(name: str) -> UnicatDefinition | None
unicat.get_definitions_by_name(names: list[str]) -> dict[str, UnicatDefinition | None]
unicat.get_class(gid: str) -> UnicatClass | None
unicat.get_classes(gids: list[str]) -> list[UnicatClass]
unicat.get_class_by_name(name: str) -> UnicatClass | None
unicat.get_classes_by_name(names: list[str]) -> dict[str, UnicatClass | None]
unicat.get_field(gid: str) -> UnicatField | None
unicat.get_fields(gids: list[str]) -> list[UnicatField]
unicat.get_field_by_name(name: str) -> UnicatField | None
unicat.get_fields_by_name(names: list[str]) -> dict[str, UnicatField | None]
unicat.get_query(gid: str) -> UnicatQuery | None
unicat.get_queries(gids: list[str]) -> list[UnicatQuery]
unicat.get_record_query_by_name(name: str) -> UnicatQuery | None
unicat.get_record_queries_by_name(names: list[str]) -> dict[str, UnicatQuery | None]
unicat.get_asset_query_by_name(name: str) -> UnicatQuery | None
unicat.get_asset_queries_by_name(names: list[str]) -> dict[str, UnicatQuery | None]
unicat.get_schema_query_by_name(name: str) -> UnicatQuery | None
unicat.get_schema_queries_by_name(names: list[str]) -> dict[str, UnicatQuery | None]
unicat.get_all_module_names() -> list[str]  # New in v0.7.9
unicat.get_module(name: str, *, force: bool) -> UnicatModule | None  # New in v0.7.9
unicat.get_modules(names: list[str], *, force: bool) -> list[UnicatModule]  # New in v0.7.9
```

### Traversing methods

```python
unicat.walk_record_children(parent_record: UnicatRecord, channel: gid, ordering: gid) -> Iterator[UnicatRecord]
unicat.walk_record_tree(channel: gid, ordering: gid) -> Iterator[UnicatRecord]
unicat.walk_record_query(language: str, query: UnicatQuery, *, limit: int) -> Iterator[tuple[int, UnicatRecord]]
unicat.walk_asset_children(parent_asset: UnicatAsset) -> Iterator[UnicatAsset]
unicat.walk_asset_tree() -> Iterator[UnicatAsset]
unicat.walk_asset_query(language: str, query: UnicatQuery, *, limit: int) -> Iterator[tuple[int, UnicatAsset]]
unicat.walk_definitions() -> Iterator[UnicatDefinition]
unicat.walk_classes() -> Iterator[UnicatClass]
unicat.walk_fields() -> Iterator[UnicatField]
unicat.walk_schema_query(language: str, query: UnicatQuery, *, limit: int) -> Iterator[tuple[int, UnicatQuery]]
unicat.walk_queries() -> Iterator[UnicatQuery]
unicat.walk_modules() -> Iterator[UnicatModule]  # New in v0.7.9
```

### Properties

```python
unicat.project: UnicatProject
```

### `UnicatProject` properties & methods

```python
project.gid: gid
project.name: str
project.owner: UnicatUser
project.icon: str  # used to construct /media url
project.status: str
project.languages: list[str]
project.default_language: str
project.channels: dict[str, gid]
project.default_channel: gid
project.channel_name(key: gid) -> str
project.orderings: dict[str, gid]
project.default_ordering: gid
project.ordering_name(key: gid) -> str
project.fieldlists: dict[str, gid]
project.default_fieldlist: gid
project.fieldlist_name(key: gid) -> str
project.backups: list[UnicatProjectBackup]
project.get_backup(version: int) -> UnicatProjectBackup | None
project.members: list[UnicatProjectMember]
```

### `UnicatUser` properties & methods

```python
user.gid: gid
user.username: str
user.name: str
user.avatar: str  # used to construct /media url
```

### `UnicatProjectMember` properties & methods

```python
projectmember.project: UnicatProject
projectmember.user: UnicatUser
projectmember.status: str
projectmember.roles: list[str]
projectmember.options: dict
projectmember.key: str
```

### `UnicatProjectBackup` properties & methods

```python
backup.version: int
backup.name: str
backup.created_by: str
backup.timestamp: timestamp  # 1610635123.351925
```

### `UnicatDefinition` properties & methods

```python
definition.gid: gid
definition.original: UnicatDefinition | None
definition.name: str
definition.label: dict[str, str]  # key is language
definition.classes: list[UnicatClass]
definition.classes_as_gids: list[gid]
definition.fields: list[UnicatField]
definition.fields_as_gids: list[gid]
definition.titlefield: UnicatField
definition.fieldlists: dict[str, list[UnicatField]]  # key is fieldlist key
definition.layout: UnicatLayout
definition.childdefinitions: list[UnicatDefinition]
definition.is_base: bool
definition.is_new: bool
definition.is_extended: bool
definition.is_working_copy: bool
definition.is_committed: bool
definition.all_fields: list[UnicatField]
definition.base_classes: list[UnicatClass]
definition.base_fields: list[UnicatField]
definition.all_base_fields: list[UnicatField]
definition.extended_classes: list[UnicatClass]
definition.extended_fields: list[UnicatField]
definition.all_extended_fields: list[UnicatField]
definition.metadata: dict[str, UnicatMetadataField]
```

### `UnicatClass` properties & methods

```python
class_.gid: gid
class_.original: UnicatClass | None
class_.name: str
class_.label: dict[str, str]  # key is language
class_.fields: list[UnicatField]
class_.fields_as_gids: list[gid]
class_.layout: UnicatLayout
class_.is_new: bool
class_.is_working_copy: bool
class_.is_committed: bool
class_.metadata: dict[str, UnicatMetadataField]
```

### `UnicatField` properties & methods

```python
field.gid: gid
field.original: UnicatField | None
field.name: str
field.type: str
field.class_: UnicatClass | None
field.options: dict
field.is_localized: bool
field.is_required: bool
field.label: dict[str, str]  # key is language
field.initial: dict[str, str]  # key is language
field.unit: str
field.title: dict[str, str]  # key is language
field.is_new: bool
field.is_working_copy: bool
field.is_committed: bool
field.metadata: dict[str, UnicatMetadataField]
```

### `UnicatLayout` properties & methods

```python
layout.gid: gid
layout.original: UnicatLayout | None
layout.name: str
layout.root: gid
layout.components: dict[gid, dict]
layout.is_new: bool
layout.is_working_copy: bool
```

### `UnicatQuery` properties & methods

```python
query.gid: gid
query.type: str  # schema, record, or asset
query.name: str
query.q: str
query.filter: list
```

### `UnicatAsset` properties & methods

```python
asset.gid: gid
asset.pathname: str
asset.path: str
asset.name: str
asset.is_file: bool
asset.type: str
asset.childcount: int
asset.status: str
asset.is_deleted: bool
asset.info: dict
asset.transforms: dict[str, dict] | None
asset.default_transform: dict | None
asset.title: dict[str, str]  # key is language
asset.description: dict[str, str]  # key is language
asset.created_on: timestamp  # 1610635123.351925
asset.updated_on: timestamp  # 1610635123.351925
asset.publish() -> str  # public_url
asset.publish_transformed(transform: UnicatTransform | None) -> str  # public_url
asset.download(pathname: str | None) -> False | None | str  # local_filepath
asset.download_transformed(transform: UnicatTransform | None, pathname: str | None) -> False | None | str  # local_filepath
```

### `UnicatRecord` properties & methods

```python
record.gid: gid
record.canonical: gid
record.parent: gid
record.backlinks: list[gid]
record.is_link: bool
record.is_deleted: bool
record.treelevel: int
record.path: list[gid]
record.title: dict[str, str]  # key is language
record.channels: list[gid]  # enabled channels only
record.orderings: dict[gid, int]
record.childcount: int
record.definition: UnicatDefinition
record.created_on: timestamp  # 1610635123.351925
record.updated_on: timestamp  # 1610635123.351925
record.fields: dict[str, dict[str, UnicatRecordField]]  # key is language, then fieldname
record.validation_report: None | list[dict[str, Any]]  # validation result after updates
```

### `UnicatRecordField` properties & methods

```python
recordfield.field: UnicatField
recordfield.value: Any
recordfield.key: None | str
```

A record field can have a value, a reference (record, asset), or it can be nested for class-fields. \
We also support 'list' versions of these.

For textline/textlist fields that have a values option (a selection of values to choose from), the `key` property holds the key, and the `value` property holds the label (unless value_labels is disabled for that field, then `value` holds the key too). The `key` is `None` in all other cases.

```python
# for values

artnr = record.fields[language]["artnr"]  # a recordfield
artnr.value             # "CMS 225-945"
artnr.field.label       # "Article number"
artnr.field.type        # "textline"

# for references

image = record.fields[language]["image"]  # both recordfield and asset
image.value             # "a0a80c9c-fa1b-4573-ac98-b7b07c81b583"
image.field.label       # "Image"
image.pathname          # "/products/cms225.eps"

# for class fields

dimensions_interior = record.fields[language]["dimensions_interior"]
                        # a recordfield and classfield
dimensions_interior.value               # {"width__mm": 374, …}
dimensions_interior["width__mm"].value  # 374  -- this is a recordfield

# for list values

colors = record.fields[language]["colors"]
colors.value            # ["Red", "Blue"]
colors.key              # ["r", "b"] -- not named `keys`
colors.field.label      # "Colors"
colors[0].value         # "Red" -- this is just a string
colors[0].key           # "r"

# for list references

images = record.fields[language]["images"]
images.value            # ["a0a80c9c-fa1b-4573-ac98-b7b07c81b583", ]
images.field.label      # "Images"
images[0]               # this is just an asset
images[0].pathname      # "/products/cms225.eps"

# for classlist fields

tablespecs = record.fields[language]["tablespecs"]
tablespecs.value                        # [{"width__mm": 7, …}, …]
tablespecs.field.label                  # "Table specs"
tablespecs[0]                           # this is recordfield-like
tablespecs[0]["width__mm"].value        # 7
tablespecs[0]["width__mm"].field.label  # "Width"
```


### `UnicatMetadataField` properties & methods

```python
metadata_field.name: str
metadata_field.type: str
metadata_field.is_localized: bool
metadata_field.value: None | Any | dict(str, None | Any)  # key is language
```

A metadata field can have a value or a reference (asset, field), and it can be localized. If you need the gid for the reference and don't want it to automatically make an API call, use the underlying `metadata_field._value` to get it.

```python
# example field

artnr = unicat.get_field_by_name("artnr")

# for values

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
```

### `UnicatModule` properties & methods

New in v0.7.9

```python
module.name: str
module.version: str  # in 1.2.3 format
module.keys: dict(str, Any)
module.actions: dict(str, UnicatModuleAction)
module.keys: list(UnicatModuleLog)
```

### `UnicatModuleAction` properties & methods

New in v0.7.9

```python
module.name: str
module.configuration: dict(str, Any)
```

### `UnicatModuleLog` properties & methods

New in v0.7.9

module.timestamp: timestamp  # 1610635123.351925
module.version: str  # in 1.2.3 format
module.action: str
module.configuration: dict(str, Any)
module.command: str
module.started_at: timestamp  # 1610635123.351925
module.ended_at: timestamp  # 1610635123.351925
module.duration: float # seconds
module.status: str
module.output: str


### Mutating project settings

```python
mutate.add_language(language: str) -> bool
mutate.remove_language(language: str) -> bool

mutate.create_channel(name: str) -> gid  # gid type is actually a string
mutate.delete_channel(gid: gid) -> bool

mutate.create_ordering(name: str) -> gid
mutate.delete_ordering(gid: gid) -> bool

mutate.create_fieldlist(name: str) -> gid
mutate.delete_fieldlist(gid: gid) -> bool
```

### Mutating definitions

```python
mutate.create_definition(*, name: str, label: dict[str, str], classes: list[UnicatClass], fields: list[UnicatField], titlefield: UnicatField, childdefinitions: list[UnicatDefinition], metadata: dict[str, UnicatMetadataField]) -> UnicatDefinition
mutate.modify_definition(definition: UnicatDefinition, *, name: str, label: dict[str, str], classes: list[UnicatClass], fields: list[UnicatField], titlefield: UnicatField, childdefinitions: list[UnicatDefinition], metadata: dict[str, UnicatMetadataField]) -> UnicatDefinition
mutate.modify_definition_modify_layout(definition: UnicatDefinition, *, name: str, root: gid, components: dict[gid, dict]) -> UnicatDefinition
mutate.modify_definition_add_class(definition: UnicatDefinition, class_: UnicatClass) -> UnicatDefinition
mutate.modify_definition_remove_class(definition: UnicatDefinition, class_: UnicatClass) -> UnicatDefinition
mutate.modify_definition_add_field(definition: UnicatDefinition, field: UnicatField) -> UnicatDefinition
mutate.modify_definition_remove_field(definition: UnicatDefinition, field: UnicatField) -> UnicatDefinition
mutate.modify_definition_fieldlist_add_field(definition: UnicatDefinition, fieldlist: gid, field: UnicatField) -> UnicatDefinition
mutate.modify_definition_fieldlist_remove_field(definition: UnicatDefinition, fieldlist: gid, field: UnicatField) -> UnicatDefinition
mutate.modify_definition_add_childdefinition(definition: UnicatDefinition, childdefinition: UnicatDefinition) -> UnicatDefinition
mutate.modify_definition_remove_childdefinition(definition: UnicatDefinition, childdefinition: UnicatDefinition) -> UnicatDefinition
mutate.modify_definition_set_metadata(definition: UnicatDefinition, name: str, *, type: str, is_localized: bool, value: Any) -> UnicatDefinition
mutate.modify_definition_clear_metadata(definition: UnicatDefinition, name: str) -> UnicatDefinition
mutate.commit_definition(new_or_working_copy: UnicatDefinition) -> UnicatDefinition
mutate.save_as_new_definition(working_copy: UnicatDefinition) -> UnicatDefinition
mutate.delete_definition(definition: UnicatDefinition) -> bool
```

### Mutating classes

```python
mutate.create_class(*, name: str, label: dict[str, str], fields: list[UnicatField], metadata: dict[str, UnicatMetadataField]) -> UnicatClass
mutate.modify_class(class_: UnicatClass, *, name: str, label: dict[str, str], fields: list[UnicatField], metadata: dict[str, UnicatMetadataField]) -> UnicatClass
mutate.modify_class_modify_layout(class_: UnicatClass, *, name: str, root: gid, components: dict[gid, dict]) -> UnicatClass
mutate.modify_class_add_field(class_: UnicatClass, field: UnicatField) -> UnicatClass
mutate.modify_class_remove_field(class_: UnicatClass, field: UnicatField) -> UnicatClass
mutate.modify_class_set_metadata(class_: UnicatClass, name: str, *, type: str, is_localized: bool, value: Any) -> UnicatClass
mutate.modify_class_clear_metadata(class_: UnicatClass, name: str) -> UnicatClass
mutate.commit_class(new_or_working_copy: UnicatClass) -> UnicatClass
mutate.save_as_new_class(working_copy: UnicatClass) -> UnicatClass
mutate.delete_class(class_: UnicatClass) -> bool
```

### Mutating fields

```python
mutate.create_field(*, name: str, type: str, is_localized: bool, is_required: bool, label: dict, unit: str, initial: dict, options: dict, metadata: dict[str, UnicatMetadataField]) -> UnicatField
mutate.modify_field(field: UnicatField, *, name: str, type: str, is_localized: bool, is_required: bool, label: dict, unit: str, initial: dict, options: dict, metadata: dict[str, UnicatMetadataField]) -> UnicatField
mutate.modify_field_set_metadata(field: UnicatField, name: str, *, type: str, is_localized: bool, value: Any) -> UnicatField
mutate.modify_field_clear_metadata(field: UnicatField, name: str) -> UnicatField
mutate.commit_field(new_or_working_copy: UnicatField) -> UnicatField
mutate.save_as_new_field(working_copy: UnicatField) -> UnicatField
mutate.delete_field(field: UnicatField) -> bool
```

### Mutating records

```python
mutate.create_record(parent: UnicatRecord, ordering: gid) -> UnicatRecord
mutate.set_record_definition(record: UnicatRecord, definition: UnicatDefinition) -> UnicatRecord
mutate.extend_record_definition_add_class(record: UnicatRecord, class_: UnicatClass) -> UnicatRecord
mutate.extend_record_definition_add_field(record: UnicatRecord, field: UnicatField) -> UnicatRecord
mutate.extend_record_definition_add_fieldlist_field(record: UnicatRecord, fieldlist: gid, field: UnicatField) -> UnicatRecord
mutate.extend_record_definition_remove_class(record: UnicatRecord, class_: UnicatClass) -> UnicatRecord
mutate.extend_record_definition_remove_field(record: UnicatRecord, field: UnicatField) -> UnicatRecord
mutate.extend_record_definition_remove_fieldlist_field(record: UnicatRecord, fieldlist: gid, field: UnicatField) -> UnicatRecord
mutate.revert_extended_record_definition(record: UnicatRecord) -> UnicatRecord  # New in v0.7.12
mutate.copy_record_definition_to_siblings(record: UnicatRecord) -> None  # New in v0.7.12
mutate.update_record(record: UnicatRecord, localizedfielddata: dict) -> UnicatRecord
mutate.set_record_channels(record: UnicatRecord, channels: list[gid], enabled: bool) -> UnicatRecord
mutate.copy_record_channels_from_parent(record: UnicatRecord, channels: list[gid] | None) -> UnicatRecord
mutate.copy_record_channels_down(record: UnicatRecord, channels: list[gid] | None, return_job: Bool = False) -> UnicatRecord | UnicatJob
mutate.copy_record_channels_up(record: UnicatRecord, channels: list[gid] | None) -> UnicatRecord
mutate.set_record_orderings(record: UnicatRecord, orderings: dict) -> UnicatRecord
mutate.link_record(parent: UnicatRecord, record: UnicatRecord, ordering: gid) -> UnicatRecord
mutate.delete_record(record: UnicatRecord) -> UnicatRecord
mutate.undelete_record(record: UnicatRecord) -> UnicatRecord
mutate.permanent_delete_record(record: UnicatRecord, return_job: Bool = False) -> UnicatRecord | UnicatJob
```

### Mutating assets

```python
mutate.upload_asset(localfilepath: Path | str, folderasset: UnicatAsset) -> UnicatAsset
mutate.upload_update_asset(localfilepath: Path | str, asset: UnicatAsset) -> UnicatAsset
mutate.create_asset(parentasset: UnicatAsset, name: str) -> UnicatAsset
mutate.update_asset(asset: UnicatAsset, name: str, title: dict, description: dict) -> UnicatAsset
mutate.delete_asset(asset: UnicatAsset) -> UnicatAsset
mutate.undelete_asset(asset: UnicatAsset) -> UnicatAsset
mutate.permanent_delete_asset(asset: UnicatAsset) -> bool
```

### Mutating queries

```python
mutate.create_query(type: str, name: str, q: str, filter: list) -> UnicatQuery
mutate.update_query(query: UnicatQuery, name: str, q: str, filter: list) -> UnicatQuery
mutate.delete_query(query: UnicatQuery) -> bool
```

### Modules

New in v0.7.9

```python
mutate.register_module(name: str, version: str) -> UnicatModule
mutate.unregister_module(module: UnicatModule) -> bool
mutate.set_module_key(module: UnicatModule, key: str, value: Any) -> UnicatModule
mutate.set_module_keys(module: UnicatModule, keyvalues: dict(str, Any)) -> UnicatModule
mutate.clear_module_key(module: UnicatModule, key: str) -> UnicatModule
mutate.clear_module_keys(module: UnicatModule, keys: list(str)) -> UnicatModule
mutate.publish_module_action(module: UnicatModule, action: str, configuration: dict(str, Any)) -> UnicatModule
mutate.unpublish_module_action(module: UnicatModule, action: str) -> UnicatModule
mutate.add_module_log(module: UnicatModule, version: str,  action: str, configuration: dict(str, Any), command: str, started_at: timestamp,  ended_at: timestamp,  status: str, output: str) -> UnicatModule
```

### Backups

```python
mutate.create_backup(created_by: str, name: str, return_job: Bool = False) -> UnicatProjectBackup | UnicatJob
mutate.update_backup(backup: UnicatProjectBackup, name: str) -> UnicatProjectBackup
mutate.restore_backup(backup: UnicatProjectBackup, return_job: Bool = False) -> UnicatProject | UnicatJob
mutate.delete_backup(backup: UnicatProjectBackup) -> UnicatProject
mutate.delete_backups(backups: list[UnicatProjectBackup]) -> UnicatProject
```


### Jobs

Some mutating methods can return a job if requested, so you can choose to wait for completion yourself (`track` method), or ignore it and let it finish in the background some time. The job always has the `return_value` from the (mutating) method available -- this is the "immediately returned" value, not some result from running the actual job (look in `status` and `info` instead).

Usage:

```python
# by default, the method waits for completion before returning
record = unicat.mutate.copy_record_channels_down(record, channels)

# but you can also track progress yourself
job = unicat.mutate.copy_record_channels_down(record, channels, return_job=True)
for status in job.track():
    assert status == job.status
    print(job.name, job.status)
record = job.return_value

# or, return quickly and let the job run unmonitored in the background
job = unicat.mutate.copy_record_channels_down(record, channels, return_job=True)
record = job.return_value
```

#### `UnicatJob` properties & methods

```python
job.gid: gid
job.name: str
job.status: str
job.info: dict
job.created_on: timestamp | None
job.updated_on: timestamp | None
job.progress: dict  # combined gid, name, status, info, and timestamps
job.return_value: Any
job.track(timeout_in_seconds: float | None = None, poll_interval_in_seconds: float = 1.0) -> Generator[str]
```


### Error handling

We handle errors with the `UnicatError` exception.

```python
from unicat import Unicat, UnicatError
from config import PROJECT_GID, SECRET_API_KEY, LOCAL_ASSET_FOLDER

unicat = Unicat("https://unicat.app", PROJECT_GID, SECRET_API_KEY, LOCAL_ASSET_FOLDER)
if not unicat.connect():
    raise Exception("Invalid connection settings")

...

try:
    unicat.mutate.update_record(record, {language: fields_data})
except UnicatError as e:
    print(e, e.code, e.message, e.info)
```

The `.code`, `.message`, and `.info` properties match the API error result.


### Asset transform helper

```python
from unicat import UnicatTransform
```

We use this on assets, for publishing and/or downloading transformed versions.

```python
transform = UnicatTransform(resize="fill", width=400, height=300, type="jpg", dpr=2, optimize=True)

public_url = asset.publish_transformed(transform)

transform.merge(UnicatTransform(width=200, height=200, key="thumb")) # keeps type, dpr, etc

local_pathname = asset.download_transformed(transform)
```

A `UnicatTransfrom` accepts any combination of the following arguments.

```text
name
key
force
optimize
resize
width
height
type
hotspot
crop
padding
quality
background
dpr
```

Each argument explained:

    name = "seo-optimized-name"

Default: use source filename \
Use this as the filename instead of the source filename. Mustn't include the extension.

    key = "2x"

Default: auto-generate a key from a hash of the options \
If you make multiple transforms from the same file, you can use keys to individualize them. They are included in the filename after the name and before the extension. A key is prepended by a '@', so we would get /filename@2x.jpg. You can use @'s in filenames and in keys, just make sure that the combinations add up to a unique final filename.

    type = "jpg"

Options: jpg, png, or gif \
Both extension and transformed file type. If you don't specify this, the source extension is used, which can lead to faulty results if it isn't one of the supported file types (jpg, png, or gif).

    force = True

Default: False \
If force isn't enabled, no transformation is done if a file with the transform filename exists and is newer than the source.

    optimize = True

Default: False \
We support pngcrush, jhead, jpegoptim, jpeg-recompress, gifsicle, scour, and svgo to strip down and compress the transformed file. Since this is a time-consuming process, it is disabled by default.

    resize = "fill"

Options: width, height, fit, or fill \
Resizing will always respect the aspect ratio. Placement of the resized source on the canvas is controlled by the width, height, hotspot, crop, and padding options. Images are never scaled up, only down.

    width = 400

Resulting width of the transformed asset, in logical pixels (see also `dpr`).

Value is capped at 5000 pixels.

    height = 300

Resulting height of the transformed asset, in logical pixels (see also `dpr`).

Value is capped at 5000 pixels.

    hotspot = (0.5, 0.5)

Default: 0.5,0.5 (the center) \
The hotspot serves two purposes: first to place the resized image on the canvas with the hotspot as close as possible to the center of the canvas, and second as the centerpoint for the crop transform if one is requested.
The hotspot is given as an x,y coordinate, with values as a fraction of the width and height, respectively. Valid values are 0.0 through 1.0 for each.

    crop = (0.6, 0.6)

Default: don't crop \
Use crop to select an area from the source that will then be resized to be placed on the canvas. The crop is centered on the hotspot.
The crop is given as w,h dimensions, with values as a fraction of the width and height, respectively. Valid values are 0.0 through 1.0 for each.

    padding = (0, "auto", 0, "auto")

Default: `auto`,`auto`,`auto`,`auto` \
Specify padding in the target image. The values are for top, right, bottom, and left padding (clockwise starting at top). If a value is set to `auto`, that padding will grow to fill available space. If two opposing sides have non-`auto` values, they will get at least the specified padding, plus half of the remaining available space each. If you want to anchor the image to the top-right of the canvas, you can specify 0,0,"auto","auto".

Values are capped at 1000 pixels.

    background = "abcdef"

Default: transparent (or white if transformed file doesn't support transparency) \
Specify a background color to use for transparent areas in the source and for any padding added.
There are two predefined options, `transparent` and `white`. Any other background color must be specified as an rgb hex value, similar to CSS but without the \# sign. Use the full 6-character rgb hex, not a CSS shortcut like bbb.

    quality = 82

Default: 100 \
Lower quality leads to smaller filesizes, but higher quality looks better. This is a compromise, use your best judgment.
Allowed values are 0 through 100.

    dpr = 2

Default: 1 \
Device pixel ratio is abbreviated dpr, and is used to indicate the number of physical pixels the device screen has per logical pixel. You always specify the resizing and padding values in logical pixels. Regular screens have a dpr of 1. High resolution or retina screens have a dpr of 2 or 3. We support a max dpr of 4, just in case. A dpr of 2 means that for a requested width of 400, you get a transformed image with 800 (physical) pixels.



### `unicat.utils`

```python
from unicat.utils import *
```


```python
def gid() -> str  # a uuid4

def maybe_gid(possible_gid: Any) -> bool  # New in v0.7.10

def maybe_dotted_gid(possible_gid: Any) -> bool

def test_true(data: Any) -> bool

def test_false(data: Any) -> bool

def make_bool(any: Any) -> bool

def make_bool_str(any: Any) -> str

def make_str(any: Any) -> str

def make_json_str(any: Any) -> str

def make_json(any: Any) -> Any

def make_json_list(any: Any) -> list[Any]

def make_int(any: Any) -> int

def make_float(any: Any) -> float

def noop(any: Any) -> Any

def make_str_list(any: Any) -> list[str]

def convert_value_to_fielddata(fieldtype: str, value: Any) -> bool | str | Any | int | float | list[str] | list[Any]
    """Return a value suitable for writing to Unicat, for list field types this
    means converting newline-separated entries to lists.
    For class or classlist fields, we produce a JSON data structure.

    This can raise exceptions when the value doesn't match the type, e.g. converting a
    string to a float.
    """

def convert_fielddata_to_value(fieldtype: str, fielddata: Any) -> str | int | float
    """Return a value suitable for writing in a cell, such as a text or a number.
    Lists will be flattened by stringifying each item and concatenating with \n.
    For class or classlist fields, we will have pretty-printed JSON.
    """

def merge_dicts(a: dict, b: dict) -> dict
    """Merge b into a, returning a.

    a is updated; if you don't want to mutate a, call it as `merge_dicts(dict(a), b)`.
    """

def diff_record_fields_data(unicat: Unicat, record: UnicatRecord, localizedfielddata: dict) -> dict  # dict format: d[language][fieldname] = value
    """Return a version of localizedfielddata that only has data that is different from
    the raw record data.
    """

def hash_text(text: str) -> str  # unicode ok

def hash_data(data: Any) -> str  # data must be json-serializable

class DuckObject  # quickly construct an object-like duck from a dict or kwargs, see below

class FieldColumns  # flatten a list of (class-)fields, see below
```


### DuckObject

DuckObjects are used to quickly construct an object-like duck.

Uses keyword arguments to construct any duck-like object with those attributes.

```python
ducklike = DuckObject(walk="waddle", talk="quack")
assert ducklike.walk == "waddle"
assert ducklike.talk == "quack"
assert not hasattr(ducklike, "bill")

duckquery = DuckObject(
    q="",
    filter=["value", "is", [base_artnr_field.gid, article.base_artnr]]
)
print(duckquery.q, duckquery.filter)

duckrecord = DuckObject(gid="<anything gid-like>")
print(duckrecord.gid)
```


### FieldColumns

FieldColumns are needed for class fields, that have nested subfields.

With FieldColumns, we can flatten a list of fields to a list of columns,
associated with those fields.

Each column has a fieldstack, that is a list of the field and nested subfields.
For a regular field, the fieldstack is just that field.
A classfield with three subfields will yield three columns, and each column has
a fieldstack with the classfield first, and then the subfield for that column.
If that subfield is another classfield, we'll get more columns and deeper
stackfields.

For example, you have `[image, dimensions]` as fields, and `dimensions` is of type class, and has subfields `width` and `length`; FieldColumns will give you `[image, dimensions.width, dimensions.length]`, useable for writing to tab-separated files or spreadsheets.

Most of the time, you won't need the stackfield in the client code, see also the
\_FieldColumn implementation where we get the 'name' for a column by walking the
fieldstack.

Client code can look something like this, for reading from Unicat:

```python
columns = FieldColumns(fields, prefix_column_count=3)
for column in columns:
    column_name = column.name()  # e.g. 'image' or 'dimensions.width__mm'
    column_label = column.label()  # e.g. 'Image' or 'Dimensions\nWidth [mm]'
    column_value = None
    error = None
    try:
        record_field = column.extract_record_field(record.fields[language])
        column_value = record_field.value if record_field else None
    except KeyError:
        error = (
            "Field is not part of this definition. Do not enter data here."
        )
```

FieldColumns can also be used to write to Unicat, when we need a record's fields
data structure:

```python
recordfields_data = {}
for column in columns:
    fieldvalue = row[column.index].value
    column.update_fields_data(recordfields_data, fieldvalue)
unicat.mutate.update_record(record, {language: recordfields_data})
```


## Changelog

### v0.7.12

Adds the option to revert a record's extended definition, and the option to copy the record's definition to all other records with the same parent (the siblings).

The copy-to-siblings option is mainly used to have all records in a group share the same extended definition, so extending a record with a new field will add it to all records in that group.

```python
mutate.revert_extended_record_definition(record: UnicatRecord) -> UnicatRecord
mutate.copy_record_definition_to_siblings(record: UnicatRecord) -> None
```

### v0.7.11

Adds some type hints to improve developer experience.

### v0.7.10

Adds a utility `maybe_dotted_gid` to check whether a string may be a chain of gids, separated by dots. Also works for a single gid, but if you need only a single gid, keep using `maybe_gid`.


### v0.7.9 - module information for Unicat Connect integration

Unicat v2025.07.001 adds module information for Unicat Connect modules, allowing the modules to read and write module-related information. Multiple users can now read and write shared settings and configurations. The modules can add log entries.

We have three new classes, `UnicatModule`, `UnicatModuleAction`, and `UnicatModuleLog`.
To support these, there are four new reading methods and nine new mutating functions.

```python
unicat.get_all_module_names() -> list[str]
unicat.get_module(name: str, *, force: bool) -> UnicatModule | None
unicat.get_modules(names: list[str], *, force: bool) -> list[UnicatModule]
unicat.walk_modules() -> Iterator[UnicatModule]

mutate.register_module(name: str, version: str) -> UnicatModule
mutate.unregister_module(module: UnicatModule) -> bool
mutate.set_module_key(module: UnicatModule, key: str, value: Any) -> UnicatModule
mutate.set_module_keys(module: UnicatModule, keyvalues: dict(str, Any)) -> UnicatModule
mutate.clear_module_key(module: UnicatModule, key: str) -> UnicatModule
mutate.clear_module_keys(module: UnicatModule, keys: list(str)) -> UnicatModule
mutate.publish_module_action(module: UnicatModule, action: str, configuration: dict(str, Any)) -> UnicatModule
mutate.unpublish_module_action(module: UnicatModule, action: str) -> UnicatModule
mutate.add_module_log(module: UnicatModule, version: str, action: str, configuration: dict(str, Any), command: str, started_at: timestamp, ended_at: timestamp, status: str, output: str) -> UnicatModule
```

Another change is that a `definition`s `all_fields` and `all_base_fields` now first return the fields, and then the fields from all the classes, instead of the other way around.


### v0.7.8 - update the README to include the changelog :-)
### v0.7.7 - metadata for schema definitions, classes, and fields

Unicat v2025.04.002 adds metadata to schema definitions, classes, and fields.

On these classes, there's a new `metadata` property, that is a dict of `UnicatMetadataField` items.

For mutating, the create and modify functions for definitions, classes, and fields accept a `metadata` argument. In addition, there are six new mutating functions.

```python
mutate.modify_definition_set_metadata(definition: UnicatDefinition, name: str, *, type: str, is_localized: bool, value: Any) -> UnicatDefinition
mutate.modify_definition_clear_metadata(definition: UnicatDefinition, name: str) -> UnicatDefinition
mutate.modify_class_set_metadata(class_: UnicatClass, name: str, *, type: str, is_localized: bool, value: Any) -> UnicatClass
mutate.modify_class_clear_metadata(class_: UnicatClass, name: str) -> UnicatClass
mutate.modify_field_set_metadata(field: UnicatField, name: str, *, type: str, is_localized: bool, value: Any) -> UnicatField
mutate.modify_field_clear_metadata(field: UnicatField, name: str) -> UnicatField
```


### v0.7.6 - field values key/label compatibility and robustification

Unicat v2025.01.001 adds keys to the field 'values' option, so each value has a key and a localized label. This version of the Unicat Python library fully supports that, and adds a `.key` property to a `RecordField` (if applicable).

The walk_* functions now throw on error, for example when the API returns an unexpected 500 error.

The retry mechanism will now also retry on status 500, 502, 503, and 504 (with exponential backoff and max # of tries)

Optional `limit` argument for walk_*_query methodes now uses that exact value, within a range of 1 to 1000, and it has a default of 100.

Fix error when accessing `.original` on a new definition, class, or field.


### v0.7.5 - add 'remove' methods for mutating extended definitions

```python
mutate.extend_record_definition_remove_class(record: UnicatRecord, class_: UnicatClass) -> UnicatRecord
mutate.extend_record_definition_remove_field(record: UnicatRecord, field: UnicatField) -> UnicatRecord
mutate.extend_record_definition_remove_fieldlist_field(record: UnicatRecord, fieldlist: gid, field: UnicatField) -> UnicatRecord
```


### v0.7.4 - test_false adds some 'no' translations

Specifically, 'nee' (Dutch), 'nein' (German), and 'non' (French) are now interpreted as false. Also, 'nil' is interpreted as false.

This affects test_true as well, since it is implemented as `not test_false`.


### v0.7.3 - assetlist/recordlist reference fix

In rare cases an assetlist or recordlist field can have references to assets or records that no longer exist. This used to throw a UnicatError for the entire list, but now it returns None for that specific item, so you can still use the rest of the items.


### v0.7.2 - sync improvements

A new sync() method that brings the local storage in sync with the server. Raises `UnicatError` on error.

```python
unicat.sync() -> True
```

Internally, the return value for api.sync() changed from `None` to a tuple `(bool, result)`. The boolean indicates failure or success. On failure, result holds a standard Unicat error response . On success, the result is a boolean that indicates if we're in sync (True), or if there's more data to be synced (False).


### v0.7.1 - download performance fix

If pathname is given for a (transformed) download, updated_on is checked earlier, so a transform call (which is fairly expensive) can be skipped.


### v0.7.0 - s_by_(path)name fix and cleanup

Renamed `get_assets_by_pathnames` to `get_assets_by_pathname`, and changed the return
value to a dict keyed by pathname, for consistency with other by_name functions.

```python
unicat.get_assets_by_pathname(pathnames: list[str], *, force: bool) -> dict[str, UnicatAsset]
```

Fixed docs for by_name functions that fetch multiple items - they return dicts keyed by
name. Fixed returned values for those to return empty dicts when the names list is
empty.

```python
unicat.get_definitions_by_name(names: list[str]) -> dict[str, UnicatDefinition]
unicat.get_classes_by_name(names: list[str]) -> dict[str, UnicatClass]
unicat.get_fields_by_name(names: list[str]) -> dict[str, UnicatField]
unicat.get_record_queries_by_name(names: list[str]) -> dict[str, UnicatQuery]
unicat.get_asset_queries_by_name(names: list[str]) -> dict[str, UnicatQuery]
unicat.get_schema_queries_by_name(names: list[str]) -> dict[str, UnicatQuery]
```

Fixed `walk_schema_query` crash.

Fixed error-reporting from a UnicatJob gone wrong.


### v0.6.0 - backups

New project properties and methods

```python
project.backups: list[UnicatProjectBackup]
project.get_backup(version: int) -> UnicatProjectBackup | None
```

New UnicatProjectBackup class

```python
backup.version: int
backup.name: str
backup.created_by: str
backup.timestamp: timestamp  # 1610635123.351925
```

New mutation methods

```python
mutate.create_backup(created_by: str, name: str, return_job: Bool = False) -> UnicatProjectBackup | UnicatJob
mutate.update_backup(backup: UnicatProjectBackup, name: str) -> UnicatProjectBackup
mutate.restore_backup(backup: UnicatProjectBackup, return_job: Bool = False) -> UnicatProject | UnicatJob
mutate.delete_backup(backup: UnicatProjectBackup) -> UnicatProject
mutate.delete_backups(backups: list[UnicatProjectBackup]) -> UnicatProject
```


### v0.5.6 - all the things that came before we had a changelog

All the things that came before
