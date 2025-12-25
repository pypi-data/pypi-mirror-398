from .api import UnicatApi
from .asset import UnicatAsset
from .class_ import UnicatClass
from .definition import UnicatDefinition
from .error import UnicatError
from .field import UnicatField
from .module import UnicatModule
from .mutate import UnicatMutate
from .project import UnicatProject
from .query import UnicatQuery
from .record import UnicatRecord
from .transform import transformAsOptions
from .utils import Features, MockFeatures


class Unicat:
    """Higher-level Unicat API.

    Includes helpers for walking the tree, asset tree, and query results."""

    def __init__(self, unicat_url, project_gid, secret_api_key, asset_folder):
        self._unicat_url = unicat_url
        self._project_gid = project_gid
        self._secret_api_key = secret_api_key
        self.api = UnicatApi(self._unicat_url, self._project_gid, asset_folder)
        self.users = self.api.data["cc.users"]
        self.projects = self.api.data["cc.projects"]
        self.projects_members = self.api.data["cc.projects_members"]
        self.languages = self.api.data["cc.languages"]
        self.records = self.api.data["records"]
        self.definitions = self.api.data["definitions"]
        self.classes = self.api.data["classes"]
        self.fields = self.api.data["fields"]
        self.layouts = self.api.data["layouts"]
        self.assets = self.api.data["assets"]
        self.assets_by_pathname = self.api.data["assets_by_pathname"]
        self.queries = self.api.data["queries"]
        self.modules = self.api.data["modules"]
        self._definitions_by_name = {}
        self._classes_by_name = {}
        self._fields_by_name = {}
        self._queries_by_type_name = {}
        self._features = MockFeatures()
        # self.mutate = UnicatMutate(self)

    def connect(self):
        success, result = self.api.connect(self._secret_api_key)
        self._features = Features(self)
        self.mutate = UnicatMutate(self)
        return success

    def sync(self):
        while True:
            success, result = self.api.sync()
            if not success:
                raise UnicatError("sync", result)
            if result:
                break
        return True

    @property
    def version(self):
        from . import __version__

        return __version__

    @property
    def api_version(self):
        return self.api.cc_version

    @property
    def project(self):
        return UnicatProject(self, self._project_gid)

    def get_record(self, gid, *, force=False):
        if not gid:
            return None
        if gid not in self.records or force:
            success, result = self.api.call("/records/get", {"record": gid})
            if not success:
                raise UnicatError("get_record", result)
        record = UnicatRecord(self, gid)
        return record

    def get_records(self, gids, *, force=False):
        if not len(gids):
            return []
        if not self.records.keys() >= set(gids) or force:
            success, result = self.api.call("/records/get", {"records": gids})
            if not success:
                raise UnicatError("get_records", result)
            records = [UnicatRecord(self, gid) for gid in result["records"]]
        else:
            records = [UnicatRecord(self, gid) for gid in gids]
        return records

    def get_root_record(self):
        success, result = self.api.call("/records/root")
        if not success:
            raise UnicatError("get_root_record", result)
        root_record = UnicatRecord(self, result["root"])
        return root_record

    def get_asset(self, gid, *, force=False):
        if not gid:
            return None
        if gid not in self.assets or force:
            success, result = self.api.call("/assets/get", {"asset": gid})
            if not success:
                raise UnicatError("get_asset", result)
        asset = UnicatAsset(self, gid)
        return asset

    def get_asset_by_pathname(self, pathname, *, force=False):
        if not pathname:
            return None
        if pathname not in self.assets_by_pathname or force:
            success, result = self.api.call("/assets/get", {"pathname": pathname})
            if not success:
                raise UnicatError("get_asset_by_pathname", result)
            asset = UnicatAsset(self, result["asset"])
        else:
            asset = UnicatAsset(self, self.assets_by_pathname[pathname]["gid"])
        return asset

    def get_assets(self, gids, *, force=False):
        if not len(gids):
            return []
        if not self.assets.keys() >= set(gids) or force:
            success, result = self.api.call("/assets/get", {"assets": gids})
            if not success:
                raise UnicatError("get_assets", result)
            assets = [UnicatAsset(self, gid) for gid in result["assets"]]
        else:
            assets = [UnicatAsset(self, gid) for gid in gids]
        return assets

    def get_assets_by_pathname(self, pathnames, *, force=False):
        if not len(pathnames):
            return {}
        if not self.assets_by_pathname.keys() >= set(pathnames) or force:
            success, result = self.api.call("/assets/get", {"pathnames": pathnames})
            if not success:
                raise UnicatError("get_assets_by_pathname", result)
            assets = [UnicatAsset(self, gid) for gid in result["assets"]]
        else:
            assets = [
                UnicatAsset(self, self.assets_by_pathname[pathname]["gid"])
                for pathname in pathnames
            ]
        return {asset.pathname: asset for asset in assets}

    def get_root_asset(self):
        success, result = self.api.call("/assets/root")
        if not success:
            raise UnicatError("get_root_asset", result)
        root_asset = UnicatAsset(self, result["root"])
        return root_asset

    def get_definition(self, gid: str) -> UnicatDefinition | None:
        if not gid:
            return None
        if gid not in self.definitions:
            return None
        definition = UnicatDefinition(self, gid)
        return definition

    def get_definitions(self, gids: list[str]) -> list[UnicatDefinition]:
        if not len(gids):
            return []
        definitions = [
            UnicatDefinition(self, gid) for gid in gids if gid in self.definitions
        ]
        return definitions

    def _update_definitions_by_name(self):
        for definition in self.definitions.values():
            if not definition["is_new"] and not definition["is_working_copy"]:
                self._definitions_by_name[definition["name"]] = definition["gid"]

    def get_definition_by_name(self, name: str) -> UnicatDefinition | None:
        if not name:
            return None
        if name not in self._definitions_by_name:
            self._update_definitions_by_name()
        if name not in self._definitions_by_name:
            return None
        definition = UnicatDefinition(self, self._definitions_by_name.get(name))
        return definition

    def get_definitions_by_name(
        self, names: list[str]
    ) -> dict[str, UnicatDefinition | None]:
        if not len(names):
            return {}
        if not self._definitions_by_name.keys() >= set(names):
            self._update_definitions_by_name()
        definitions_by_name = {
            name: (
                UnicatDefinition(self, self._definitions_by_name.get(name))
                if name in self._definitions_by_name
                else None
            )
            for name in names
        }
        return definitions_by_name

    def get_class(self, gid: str) -> UnicatClass | None:
        if not gid:
            return None
        if gid not in self.classes:
            return None
        class_ = UnicatClass(self, gid)
        return class_

    def get_classes(self, gids: list[str]) -> list[UnicatClass]:
        if not len(gids):
            return []
        classes = [UnicatClass(self, gid) for gid in gids if gid in self.classes]
        return classes

    def _update_classes_by_name(self):
        for class_ in self.classes.values():
            if not class_["is_new"] and not class_["is_working_copy"]:
                self._classes_by_name[class_["name"]] = class_["gid"]

    def get_class_by_name(self, name: str) -> UnicatClass | None:
        if not name:
            return None
        if name not in self._classes_by_name:
            self._update_classes_by_name()
        if name not in self._classes_by_name:
            return None
        class_ = UnicatClass(self, self._classes_by_name.get(name))
        return class_

    def get_classes_by_name(self, names: list[str]) -> dict[str, UnicatClass | None]:
        if not len(names):
            return {}
        if not self._classes_by_name.keys() >= set(names):
            self._update_classes_by_name()
        classes_by_name = {
            name: (
                UnicatClass(self, self._classes_by_name.get(name))
                if name in self._classes_by_name
                else None
            )
            for name in names
        }
        return classes_by_name

    def get_field(self, gid: str) -> UnicatField | None:
        if not gid:
            return None
        if gid not in self.fields:
            return None
        field = UnicatField(self, gid)
        return field

    def get_fields(self, gids: list[str]) -> list[UnicatField]:
        if not len(gids):
            return []
        fields = [UnicatField(self, gid) for gid in gids if gid in self.fields]
        return fields

    def _update_fields_by_name(self):
        for field in self.fields.values():
            if not field["is_new"] and not field["is_working_copy"]:
                self._fields_by_name[field["name"]] = field["gid"]

    def get_field_by_name(self, name: str) -> UnicatField | None:
        if not name:
            return None
        if name not in self._fields_by_name:
            self._update_fields_by_name()
        if name not in self._fields_by_name:
            return None
        field = UnicatField(self, self._fields_by_name.get(name))
        return field

    def get_fields_by_name(self, names: list[str]) -> dict[str, UnicatField | None]:
        if not len(names):
            return {}
        if not self._fields_by_name.keys() >= set(names):
            self._update_fields_by_name()
        fields_by_name = {
            name: (
                UnicatField(self, self._fields_by_name.get(name))
                if name in self._fields_by_name
                else None
            )
            for name in names
        }
        return fields_by_name

    def get_query(self, gid: str) -> UnicatQuery | None:
        if not gid:
            return None
        if gid not in self.queries:
            return None
        query = UnicatQuery(self, gid)
        return query

    def get_queries(self, gids: list[str]) -> list[UnicatQuery]:
        if not len(gids):
            return []
        queries = [UnicatQuery(self, gid) for gid in gids if gid in self.queries]
        return queries

    def _query_type_name_key(self, type, name):
        return type + ":" + name

    def _query_key(self, query):
        return self._query_type_name_key(query["type"], query["name"])

    def _update_queries_by_type_name(self):
        for query in self.queries.values():
            self._queries_by_type_name[self._query_key(query)] = query["gid"]

    def _get_query_by_type_name(self, type, name):
        if not name:
            return None
        key = self._query_type_name_key(type, name)
        if key not in self._queries_by_type_name:
            self._update_queries_by_type_name()
        if key not in self._queries_by_type_name:
            return None
        query = UnicatQuery(self, self._queries_by_type_name.get(key))
        return query

    def _get_queries_by_type_name(self, type, names):
        if not len(names):
            return {}
        keys_by_name = {name: self._query_type_name_key(type, name) for name in names}
        if not self._queries_by_type_name.keys() >= set(keys_by_name.values()):
            self._update_queries_by_type_name()
        queries_by_name = {
            name: (
                UnicatQuery(
                    self,
                    self._queries_by_type_name.get(
                        self._query_type_name_key(type, name)
                    ),
                )
                if self._query_type_name_key(type, name) in self._queries_by_type_name
                else None
            )
            for name in names
        }
        return queries_by_name

    def get_record_query_by_name(self, name: str) -> UnicatQuery | None:
        return self._get_query_by_type_name("record", name)

    def get_record_queries_by_name(
        self, names: list[str]
    ) -> dict[str, UnicatQuery | None]:
        return self._get_queries_by_type_name("record", names)

    def get_asset_query_by_name(self, name: str) -> UnicatQuery | None:
        return self._get_query_by_type_name("asset", name)

    def get_asset_queries_by_name(
        self, names: list[str]
    ) -> dict[str, UnicatQuery | None]:
        return self._get_queries_by_type_name("asset", names)

    def get_schema_query_by_name(self, name: str) -> UnicatQuery | None:
        return self._get_query_by_type_name("schema", name)

    def get_schema_queries_by_name(
        self, names: list[str]
    ) -> dict[str, UnicatQuery | None]:
        return self._get_queries_by_type_name("schema", names)

    def get_all_module_names(self):
        if not self._features.modules:
            raise AttributeError(
                f"'{self.__class__.__name__}' object has no attribute 'get_all_module_names' (requires Unicat API version 2025.07.001)."
            )

        success, result = self.api.call("/modules/all")
        if not success:
            raise UnicatError("get_all_module_names", result)
        return result["module_names"]

    def get_module(self, name, *, force=False):
        if not self._features.modules:
            raise AttributeError(
                f"'{self.__class__.__name__}' object has no attribute 'get_module' (requires Unicat API version 2025.07.001)."
            )

        if not name:
            return None
        if name not in self.modules or force:
            success, result = self.api.call("/modules/get", {"module": name})
            if not success:
                raise UnicatError("get_module", result)
        module = UnicatModule(self, name)
        return module

    def get_modules(self, names, *, force=False):
        if not self._features.modules:
            raise AttributeError(
                f"'{self.__class__.__name__}' object has no attribute 'get_modules' (requires Unicat API version 2025.07.001)."
            )

        if not len(names):
            return []
        if not self.modules.keys() >= set(names) or force:
            success, result = self.api.call("/modules/get", {"modules": names})
            if not success:
                raise UnicatError("get_modules", result)
            modules = [UnicatModule(self, name) for name in result["modules"]]
        else:
            modules = [UnicatModule(self, name) for name in names]
        return modules

    def publish_asset(self, asset):
        if not asset.is_file:
            return None
        success, result = self.api.publish(asset._data)
        if not success:
            raise UnicatError("publish_asset", result)
        return result["public_url"]

    def publish_transformed_asset(self, asset, transform=None):
        if not asset.is_file:
            return None
        options = transformAsOptions(transform)
        success, result = self.api.transform(asset._data, options=options)
        if not success:
            raise UnicatError("publish_transformed_asset", result)
        return result["public_url"]

    def download_asset(self, asset, pathname=None, updated_on=None):
        if not asset.is_file:
            return None
        pathname = self.api.download(
            asset._data, pathname=pathname, updated_on=updated_on
        )
        return pathname

    def download_transformed_asset(
        self, asset, transform=None, pathname=None, updated_on=None
    ):
        if not asset.is_file:
            return None
        options = transformAsOptions(transform)
        pathname = self.api.download_transformed(
            asset._data, options=options, pathname=pathname, updated_on=updated_on
        )
        return pathname

    def walk_record_children(self, parent_record, channel=None, ordering=None):
        top = 0
        size = 100
        while True:
            data = {
                "record": parent_record.gid,
                "page.top": top,
                "page.size": size,
            }
            if channel is not None:
                data["channel"] = channel
            if ordering is not None:
                data["ordering"] = ordering
            success, result = self.api.call("/records/children", data)
            if not success:
                raise UnicatError("walk_record_children", result)
            if not result["children"]:
                return
            for record_gid in result["children"]:
                record = UnicatRecord(self, record_gid)
                yield record
            top += size
            if top >= result["children.size"]:  # know when to stop
                break

    def walk_record_tree(self, channel=None, ordering=None):
        success, result = self.api.call("/records/root")
        if not success:
            raise UnicatError("walk_record_tree", result)
        root_record = UnicatRecord(self, result["root"])
        yield root_record
        yield from self._walk_record_tree_depth_first(
            root_record.gid, channel=channel, ordering=ordering
        )

    def _walk_record_tree_depth_first(self, parent_gid, channel=None, ordering=None):
        top = 0
        size = 100
        while True:
            data = {
                "record": parent_gid,
                "page.top": top,
                "page.size": size,
            }
            if channel is not None:
                data["channel"] = channel
            if ordering is not None:
                data["ordering"] = ordering
            success, result = self.api.call("/records/children", data)
            if not success:
                raise UnicatError("walk_record_tree", result)
            if not result["children"]:
                return
            for record_gid in result["children"]:
                record = UnicatRecord(self, record_gid)
                yield record
                if record.childcount > 0:
                    yield from self._walk_record_tree_depth_first(
                        record.gid, channel=channel, ordering=ordering
                    )
            top += size
            if top >= result["children.size"]:  # know when to stop
                break

    def walk_record_query(self, language, query, *, limit=None):
        request = {
            "selection": [
                {
                    "search": {
                        "language": language,
                        "q": query.q,
                        "filter": query.filter,
                    }
                },
            ],
            "page.size": min(max(1, limit if limit else 100), 1000),
        }
        result_count = 0
        while True:
            success, result = self.api.call("/records/bulk/get", request)
            if not success:
                raise UnicatError("walk_record_query", result)
            for record_gid in result["records"]:
                yield result["records.size"], UnicatRecord(self, record_gid)
                result_count += 1
                if limit and result_count >= limit:
                    return
            if not result["page.cursor"]:
                break
            request["page.cursor"] = result["page.cursor"]

    def walk_asset_children(self, parent_asset):
        top = 0
        size = 100
        while True:
            data = {
                "asset": parent_asset.gid,
                "page.top": top,
                "page.size": size,
            }
            success, result = self.api.call("/assets/children", data)
            if not success:
                raise UnicatError("walk_asset_children", result)
            if not result["children"]:
                return
            for asset_gid in result["children"]:
                asset = UnicatAsset(self, asset_gid)
                yield asset
            top += size
            if top >= result["children.size"]:  # know when to stop
                break

    def walk_asset_tree(self):
        success, result = self.api.call("/assets/root")
        if not success:
            raise UnicatError("walk_asset_tree", result)
        root_asset = UnicatAsset(self, result["root"])
        yield root_asset
        yield from self._walk_asset_tree_depth_first(root_asset.gid)

    def _walk_asset_tree_depth_first(self, parent_gid):
        top = 0
        size = 100
        while True:
            data = {
                "asset": parent_gid,
                "page.top": top,
                "page.size": size,
            }
            success, result = self.api.call("/assets/children", data)
            if not success:
                raise UnicatError("walk_asset_tree", result)
            if not result["children"]:
                return
            for asset_gid in result["children"]:
                asset = UnicatAsset(self, asset_gid)
                yield asset
                if asset.childcount > 0:
                    yield from self._walk_asset_tree_depth_first(asset.gid)
            top += size
            if top >= result["children.size"]:  # know when to stop
                break

    def walk_asset_query(self, language, query, *, limit=None):
        request = {
            "selection": [
                {
                    "search": {
                        "language": language,
                        "q": query.q,
                        "filter": query.filter,
                    }
                },
            ],
            "page.size": min(max(1, limit if limit else 100), 1000),
        }
        result_count = 0
        while True:
            success, result = self.api.call("/assets/bulk/get", request)
            if not success:
                raise UnicatError("walk_asset_query", result)
            for asset_gid in result["assets"]:
                yield result["assets.size"], UnicatAsset(self, asset_gid)
                result_count += 1
                if limit and result_count >= limit:
                    return
            if not result["page.cursor"]:
                break
            request["page.cursor"] = result["page.cursor"]

    def walk_queries(self):
        for gid in list(self.queries):
            yield UnicatQuery(self, gid)

    def walk_definitions(self):
        for gid in list(self.definitions):
            yield UnicatDefinition(self, gid)

    def walk_classes(self):
        for gid in list(self.classes):
            yield UnicatClass(self, gid)

    def walk_fields(self):
        for gid in list(self.fields):
            yield UnicatField(self, gid)

    def walk_schema_query(self, language, query, *, limit=None):
        request = {
            "selection": [
                {
                    "search": {
                        "language": language,
                        "q": query.q,
                        "filter": query.filter,
                    }
                },
            ],
            "page.size": min(max(1, limit if limit else 100), 1000),
        }
        UnicatSchemaItem = {
            "definition": UnicatDefinition,
            "class": UnicatClass,
            "field": UnicatField,
        }
        result_count = 0
        while True:
            success, result = self.api.call("/schema/bulk/get", request)
            if not success:
                raise UnicatError("walk_schema_query", result)
            for schema_item in result["schema_items"]:
                yield (
                    result["schema_items.size"],
                    UnicatSchemaItem[schema_item["type"]](self, schema_item["item"]),
                )
                result_count += 1
                if limit and result_count >= limit:
                    return
            if not result["page.cursor"]:
                break
            request["page.cursor"] = result["page.cursor"]

    def walk_modules(self):
        module_names = self.get_all_module_names()
        for module in self.get_modules(module_names):
            yield module
