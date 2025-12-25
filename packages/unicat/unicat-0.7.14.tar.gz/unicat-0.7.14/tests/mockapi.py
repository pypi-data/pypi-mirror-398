from datetime import datetime

from unicat import UnicatError
from unicat.utils import hash_data

# Data as it is returned from Unicat, then stored in the UnicatApi
MockProjectData = {
    "cc.users": {
        "<user-1>": {
            "gid": "<user-1>",
            "username": "user-1",
            "name": "User the First",
            "avatar": "user-1-avatar.png",
        }
    },
    "cc.projects": {
        "<project-1>": {
            "gid": "<project-1>",
            "name": "Project the First",
            "icon": "project-1-icon.jpg",
            "owner": "<user-1>",
            "status": "active",
            "options": {
                "timezone": "Europe/Amsterdam",
                "languages": [
                    "en",
                    "nl",
                ],
                "channels": {
                    "__all__": "[all records]",
                    "<channel-1>": "Channel the First",
                    "<channel-2>": "Channel the Second",
                },
                "orderings": {
                    "<ordering-1>": "Ordering the First",
                },
                "fieldlists": {
                    "<fieldlist-1>": "Fieldlist the First",
                },
                "orderedchannels": [
                    "__all__",
                    "<channel-1>",
                    "<channel-2>",
                ],
                "orderedorderings": [
                    "<ordering-1>",
                ],
                "orderedfieldlists": [
                    "<fieldlist-1>",
                ],
            },
            "backups": {
                "versions": [
                    {
                        "version": 3,
                        "name": "Backup 3",
                        "created_by": "Unicat",
                        "timestamp": 1610635129.04762,
                    },
                    {
                        "version": 2,
                        "name": "Backup 2",
                        "created_by": "Unicat",
                        "timestamp": 1610635128.04762,
                    },
                    {
                        "version": 1,
                        "name": "Backup 1",
                        "created_by": "Unicat",
                        "timestamp": 1610635127.04762,
                    },
                    {
                        "version": 0,
                        "name": "Initial snapshot",
                        "created_by": "Unicat",
                        "timestamp": 1610635126.04762,
                    },
                ],
                "next_version": 4,
            },
            "build": 1,
        },
    },
    "cc.projects_members": {
        "<project-1>/<user-1>": {
            "project_gid": "<project-1>",
            "user_gid": "<user-1>",
            "status": "active",
            "roles": ["owner"],
            "options": {},
        }
    },
    "cc.languages": {"en": "English", "nl": "Dutch", "it": "Italian"},
    "records": {
        "<record-0>": {
            "gid": "<record-0>",
            "parent": None,
            "canonical": "<record-0>",
            "backlinks": [],
            "treelevel": 1,
            "path": ["<record-0>"],
            "childcount": 1,
            "definition": "<definition-1>",
            "title": {"nl": "Record de Root", "en": "Record the Root"},
            "status": "published",
            "channels": [
                "__all__",
                "<channel-1>",
            ],
            "orderings": {
                "<ordering-1>": 1,
            },
            "is_link": False,
            "created_on": 1610635126.04762,
            "updated_on": 1610635126.04762,
            "fields": {
                "nl": {
                    "field-1-name": "Veld 1 waarde 0",
                    "field-2-name": "Veld 2 waarde 0",
                    "field-3-name": "Blauw",
                    "field-3-name/key": "b",
                    "field-4-name": ["Blauw"],
                    "field-4-name/key": ["b"],
                    "field-5-name": {
                        "field-3-name": "Blauw",
                        "field-3-name/key": "b",
                        "field-4-name": ["Blauw"],
                        "field-4-name/key": ["b"],
                    },
                    "field-6-name": [
                        {
                            "field-3-name": "Blauw",
                            "field-3-name/key": "b",
                            "field-4-name": ["Blauw"],
                            "field-4-name/key": ["b"],
                        }
                    ],
                },
                "en": {
                    "field-1-name": "Field 1 value 0",
                    "field-2-name": "Field 2 value 0",
                    "field-3-name": "Blue",
                    "field-3-name/key": "b",
                    "field-4-name": ["Blue"],
                    "field-4-name/key": ["b"],
                    "field-5-name": {
                        "field-3-name": "Blue",
                        "field-3-name/key": "b",
                        "field-4-name": ["Blue"],
                        "field-4-name/key": ["b"],
                    },
                    "field-6-name": [
                        {
                            "field-3-name": "Blue",
                            "field-3-name/key": "b",
                            "field-4-name": ["Blue"],
                            "field-4-name/key": ["b"],
                        }
                    ],
                },
            },
        },
        "<record-1>": {
            "gid": "<record-1>",
            "parent": "<record-0>",
            "canonical": "<record-1>",
            "backlinks": [],
            "treelevel": 2,
            "path": ["<record-1>", "<record-0>"],
            "childcount": 0,
            "definition": "<definition-1>",
            "title": {"nl": "Record de Eerste", "en": "Record the First"},
            "status": "published",
            "channels": [
                "__all__",
                "<channel-1>",
            ],
            "orderings": {
                "<ordering-1>": 1,
            },
            "is_link": False,
            "created_on": 1610635126.14762,
            "updated_on": 1610635126.14762,
            "fields": {
                "nl": {
                    "field-1-name": "Veld 1 waarde 1",
                    "field-2-name": "Veld 2 waarde 1",
                    "field-3-name": "Rood",
                    "field-3-name/key": "r",
                    "field-4-name": ["Rood"],
                    "field-4-name/key": ["r"],
                    "field-5-name": {
                        "field-3-name": "Rood",
                        "field-3-name/key": "r",
                        "field-4-name": ["Rood"],
                        "field-4-name/key": ["r"],
                    },
                    "field-6-name": [
                        {
                            "field-3-name": "Rood",
                            "field-3-name/key": "r",
                            "field-4-name": ["Rood"],
                            "field-4-name/key": ["r"],
                        }
                    ],
                },
                "en": {
                    "field-1-name": "Field 1 value 1",
                    "field-2-name": "Field 2 value 1",
                    "field-3-name": "Red",
                    "field-3-name/key": "r",
                    "field-4-name": ["Red"],
                    "field-4-name/key": ["r"],
                    "field-5-name": {
                        "field-3-name": "Red",
                        "field-3-name/key": "r",
                        "field-4-name": ["Red"],
                        "field-4-name/key": ["r"],
                    },
                    "field-6-name": [
                        {
                            "field-3-name": "Red",
                            "field-3-name/key": "r",
                            "field-4-name": ["Red"],
                            "field-4-name/key": ["r"],
                        }
                    ],
                },
            },
        },
    },
    "definitions": {
        "<definition-1>": {
            "gid": "<definition-1>",
            "original": None,
            "name": "definition-1-name",
            "label": {"nl": "Definitie 1", "en": "Definition 1"},
            "classes": ["<class-1>"],
            "fields": [
                "<field-1>",
                "<field-2>",
                "<field-3>",
                "<field-4>",
                "<field-5>",
                "<field-6>",
            ],
            "titlefield": "<field-1>",
            "fieldlists": {"<fieldlist-1>": ["<field-1>"]},
            "layout": "<layout-1>",
            "childdefinitions": [],
            "is_base": False,
            "is_new": False,
            "is_working_copy": False,
            "is_extended": False,
            "metadata": {},
        },
    },
    "classes": {
        "<class-1>": {
            "gid": "<class-1>",
            "name": "class-1-name",
            "original": None,
            "label": {"nl": "Klasse 1", "en": "Class 1"},
            "fields": ["<field-1>"],
            "layout": "<layout-2>",
            "is_new": False,
            "is_working_copy": False,
            "metadata": {},
        },
        "<class-2>": {
            "gid": "<class-2>",
            "name": "class-2-name",
            "original": None,
            "label": {"nl": "Klasse 2", "en": "Class 2"},
            "fields": ["<field-3>", "<field-4>"],
            "layout": "<layout-3>",
            "is_new": False,
            "is_working_copy": False,
            "metadata": {},
        },
    },
    "fields": {
        "<field-1>": {
            "gid": "<field-1>",
            "name": "field-1-name",
            "original": None,
            "label": {"nl": "Veld 1", "en": "Field 1"},
            "type": "text",
            "options": {},
            "is_localized": True,
            "is_required": False,
            "initial": {"nl": "", "en": ""},
            "unit": "m²",
            "is_new": False,
            "is_working_copy": False,
            "metadata": {},
        },
        "<field-2>": {
            "gid": "<field-2>",
            "name": "field-2-name",
            "original": None,
            "label": {"nl": "Veld 2", "en": "Field 2"},
            "type": "text",
            "options": {},
            "is_localized": True,
            "is_required": False,
            "initial": {"nl": "", "en": ""},
            "unit": None,
            "is_new": False,
            "is_working_copy": False,
            "metadata": {},
        },
        "<field-3>": {
            "gid": "<field-3>",
            "name": "field-3-name",
            "original": None,
            "label": {"nl": "Veld 3", "en": "Field 3"},
            "type": "textline",
            "options": {
                "value_labels": True,
                "values": [
                    {"nl": "Rood", "en": "Red", "key": "r"},
                    {"nl": "Groen", "en": "Green", "key": "g"},
                    {"nl": "Blauw", "en": "Blue", "key": "b"},
                ],
            },
            "is_localized": True,
            "is_required": False,
            "initial": {"nl": "", "en": "", "key": ""},
            "unit": None,
            "is_new": False,
            "is_working_copy": False,
            "metadata": {},
        },
        "<field-4>": {
            "gid": "<field-4>",
            "name": "field-4-name",
            "original": None,
            "label": {"nl": "Veld 4", "en": "Field 4"},
            "type": "textlist",
            "options": {
                "value_labels": True,
                "values": [
                    {"nl": "Rood", "en": "Red", "key": "r"},
                    {"nl": "Groen", "en": "Green", "key": "g"},
                    {"nl": "Blauw", "en": "Blue", "key": "b"},
                ],
            },
            "is_localized": True,
            "is_required": False,
            "initial": {"nl": "", "en": "", "key": ""},
            "unit": None,
            "is_new": False,
            "is_working_copy": False,
            "metadata": {},
        },
        "<field-5>": {
            "gid": "<field-5>",
            "name": "field-5-name",
            "original": None,
            "label": {"nl": "Veld 5", "en": "Field 5"},
            "type": "class",
            "options": {"class": "<class-2>"},
            "is_localized": False,
            "is_required": False,
            "initial": {"nl": "", "en": ""},
            "unit": None,
            "is_new": False,
            "is_working_copy": False,
            "metadata": {},
        },
        "<field-6>": {
            "gid": "<field-6>",
            "name": "field-6-name",
            "original": None,
            "label": {"nl": "Veld 6", "en": "Field 6"},
            "type": "classlist",
            "options": {"class": "<class-2>"},
            "is_localized": False,
            "is_required": False,
            "initial": {"nl": "", "en": ""},
            "unit": None,
            "is_new": False,
            "is_working_copy": False,
            "metadata": {},
        },
    },
    "layouts": {
        "<layout-1>": {
            "gid": "<layout-1>",
            "name": "layout-1-name",
            "original": None,
            "root": "<component-1>",
            "components": {"<component-1>": {"type": "vertical", "content": []}},
            "gid_map": {},
            "is_new": False,
            "is_working_copy": False,
        },
        "<layout-2>": {
            "gid": "<layout-2>",
            "name": "layout-2-name",
            "original": None,
            "root": "<component-2>",
            "components": {"<component-2>": {"type": "vertical", "content": []}},
            "gid_map": {},
            "is_new": False,
            "is_working_copy": False,
        },
        "<layout-3>": {
            "gid": "<layout-3>",
            "name": "layout-3-name",
            "original": None,
            "root": "<component-3>",
            "components": {"<component-3>": {"type": "vertical", "content": []}},
            "gid_map": {},
            "is_new": False,
            "is_working_copy": False,
        },
    },
    "assets": {
        "<asset-0>": {
            "gid": "<asset-0>",
            "pathname": "/",
            "is_file": False,
            "type": None,
            "childcount": 1,
            "status": "published",
            "info": {"filecount": 1, "foldercount": 0},
            "transforms": None,
            "path": "/",
            "name": "",
            "title": {"nl": "Asset de Root", "en": "Asset the Root"},
            "description": {"nl": "", "en": ""},
            "created_on": 1610635126.04762,
            "updated_on": 1610635126.04762,
        },
        "<asset-1>": {
            "gid": "<asset-1>",
            "pathname": "/asset-1-name.svg",
            "is_file": True,
            "type": "svg",
            "childcount": 0,
            "status": "published",
            "info": {
                "pages": 1,
                "width": 333,
                "colors": "truecolormatte",
                "format": "svg",
                "height": 333,
                "animated": False,
                "filesize": 1192,
                "metadata": {
                    "date:create": "2021-01-14T15:38:43+01:00",
                    "date:modify": "2021-01-14T15:38:43+01:00",
                },
                "colorspace": "srgb",
                "resolution": [300, 300],
                "transparent": None,
            },
            "transforms": {
                "_main_": {
                    "crop": None,
                    "hotspot": [0.6467065868263473, 0.40119760479041916],
                }
            },
            "path": "/",
            "name": "asset-1-name.svg",
            "title": {
                "nl": "Een generieke afbeelding",
                "en": "A generic image",
            },
            "description": {
                "nl": "Afbeelding - een lijntekening van een lijst met daarin bergen en de zon.",
                "en": "Image - a line drawing of a frame containing mountains and the sun.",
            },
            "created_on": 1610635126.351925,
            "updated_on": 1610635123.351925,
        },
    },
    "queries": {
        "<query-1>": {
            "gid": "<query-1>",
            "type": "record",
            "name": "query-1-record-name",
            "q": "",
            "filter": ["and", "", [["validation", "not_translated"]]],
        },
        "<query-2>": {
            "gid": "<query-2>",
            "type": "asset",
            "name": "query-2-asset-name",
            "q": "",
            "filter": ["and", "", [["validation", "any"]]],
        },
        "<query-3>": {
            "gid": "<query-3>",
            "type": "schema",
            "name": "query-3-schema-name",
            "q": "",
            "filter": ["and", "", [["is_committed", "is_true"]]],
        },
    },
    "modules": {
        "Module 1": {
            "name": "Module 1",
            "version": "1.1.1",
            "keys": {},
            "actions": {},
            "logs": [],
        },
        "Module 2": {
            "name": "Module 2",
            "version": "2.0.1",
            "keys": {},
            "actions": {},
            "logs": [],
        },
        "Module 3": {
            "name": "Module 3",
            "version": "3.2.1",
            "keys": {},
            "actions": {},
            "logs": [],
        },
    },
}


class MockApi:
    """Used to simulate regular operation of the API."""

    def __init__(self, base_url, project_gid, asset_folder=None):
        self._base_url = base_url
        self._project_gid = project_gid
        self._asset_folder = asset_folder
        self.data = MockProjectData
        self.cc_version = ""

    def connect(self, secret_api_key):
        return self._call("/auth")

    def init(self):
        return self._call("/init")

    def call(self, endpoint, data=None, method="post"):
        return self._call(endpoint, data=data)

    def upload(self, endpoint, data=None, localfilepath=None):
        return self._call_upload(endpoint, data=data)

    def publish(self, asset):
        return self._call_dam(asset)

    def transform(self, asset, options=None):
        return self._call_dam(asset)

    def download(self, asset, pathname=None, updated_on=None):
        return self._call_media(asset)

    def download_transformed(self, asset, options=None, pathname=None, updated_on=None):
        return self._call_media(asset)

    def sync(self):
        success, result = self._call_sync()
        if not success:
            return False, result
        return True, True

    def prepare_for_job(self):
        success, result = self._call_sync()
        if not success:
            return None
        return 1  # cc-cursor

    def track_job(
        self, cursor, job_gid, timeout_in_seconds=None, poll_interval_in_seconds=1.0
    ):
        now = datetime.now().timestamp()
        progress = {
            "gid": job_gid,
            "name": self.name,
            "status": "queued",
            "info": {},
            "created_on": now,
            "updated_on": now,
        }
        yield progress
        progress["status"] = "processing"
        progress["updated_on"] = now + 1
        yield progress
        progress["status"] = "processing"
        progress["updated_on"] = now + 1
        yield progress
        progress["status"] = "done"
        progress["updated_on"] = now + 1
        yield progress

    def project_member_key(self, project_member):
        return f"{project_member['project_gid']}/{project_member['user_gid']}"

    def _json_response(self, result=None):
        return True, result

    def _response_error(self, code=418, message="Mock failure", info=None):
        return False, {"code": int(code), "message": message, "info": info}

    def _call(self, endpoint, data=None):
        hash = hash_data([endpoint, data])
        print()
        print(hash, endpoint, data)
        print(flush=True)
        results = {
            hash_data(["/records/root", None]): {"root": "<record-0>"},
            hash_data(["/records/get", {"record": "<record-999>"}]): UnicatError(
                "get_record", {}
            ),
            hash_data(["/records/get", {"records": ["<record-999>"]}]): {"records": []},
            hash_data(["/assets/root", None]): {"root": "<asset-0>"},
            hash_data(["/assets/get", {"asset": "<asset-999>"}]): UnicatError(
                "get_asset", {}
            ),
            hash_data(["/assets/get", {"assets": ["<asset-999>"]}]): {"assets": []},
            hash_data(["/assets/get", {"pathname": "/asset-1-name.svg"}]): {
                "asset": "<asset-1>"
            },
            hash_data(["/assets/get", {"pathnames": ["/asset-1-name.svg"]}]): {
                "assets": ["<asset-1>"]
            },
            hash_data(["/modules/all", None]): {
                "module_names": ["Module 1", "Module 2", "Module 3"]
            },
            hash_data(["/modules/get", {"module": "Module 999"}]): UnicatError(
                "get_module", {}
            ),
            hash_data(["/modules/get", {"modules": ["Module 999"]}]): {"modules": []},
        }
        if hash not in results:
            return self._json_response(None)
        if isinstance(results[hash], UnicatError):
            raise results[hash]
        return self._json_response(results[hash])

    def _call_sync(self):
        return self._json_response()

    def _call_upload(self, endpoint, data=None):
        return self._json_response()

    def _call_dam(self, asset):
        return self._json_response(
            {"public_url": "mocks://unicat.app/p/src/any-filename.ext"}
        )

    def _call_media(self, asset):
        return "/tmp/unicat/any-filename.ext"


class MockApiFailure(MockApi):
    """Used to simulate (expected or unexpected) errors when accessing the API."""

    def _call(self, endpoint, data=None):
        return self._response_error()

    def _call_sync(self):
        return self._response_error()

    def _call_upload(self, endpoint, data=None):
        return self._response_error()

    def _call_dam(self, asset):
        return self._response_error()

    def _call_media(self, asset):
        return False
