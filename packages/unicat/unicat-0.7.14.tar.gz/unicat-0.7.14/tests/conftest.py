import pytest
from mockapi import MockApi, MockApiFailure

from unicat import Unicat
from unicat.mutate import UnicatMutate
from unicat.utils import MockFeatures

unicat_url = "mocks://unicat.app"
project_gid = "<project-1>"
secret_api_key = "<secret_api_key>"
asset_folder = "/tmp/unicat"


@pytest.fixture
def unicat():
    unicat = Unicat(unicat_url, project_gid, secret_api_key, asset_folder)
    unicat._features = MockFeatures(modules=True)
    unicat.api = MockApi(unicat_url, project_gid, asset_folder)
    unicat.users = unicat.api.data["cc.users"]
    unicat.projects = unicat.api.data["cc.projects"]
    unicat.projects_members = unicat.api.data["cc.projects_members"]
    unicat.languages = unicat.api.data["cc.languages"]
    unicat.records = unicat.api.data["records"]
    unicat.definitions = unicat.api.data["definitions"]
    unicat.classes = unicat.api.data["classes"]
    unicat.fields = unicat.api.data["fields"]
    unicat.layouts = unicat.api.data["layouts"]
    unicat.assets = unicat.api.data["assets"]
    unicat.queries = unicat.api.data["queries"]
    unicat.modules = unicat.api.data["modules"]
    unicat.mutate = UnicatMutate(unicat)
    return unicat


@pytest.fixture
def unicaterror():
    unicat = Unicat(unicat_url, project_gid, secret_api_key, asset_folder)
    unicat._features = MockFeatures(modules=True)
    unicat.api = MockApiFailure(unicat_url, project_gid, asset_folder)
    unicat.users = unicat.api.data["cc.users"]
    unicat.projects = unicat.api.data["cc.projects"]
    unicat.projects_members = unicat.api.data["cc.projects_members"]
    unicat.languages = unicat.api.data["cc.languages"]
    unicat.records = unicat.api.data["records"]
    unicat.definitions = unicat.api.data["definitions"]
    unicat.classes = unicat.api.data["classes"]
    unicat.fields = unicat.api.data["fields"]
    unicat.layouts = unicat.api.data["layouts"]
    unicat.assets = unicat.api.data["assets"]
    unicat.queries = unicat.api.data["queries"]
    unicat.modules = unicat.api.data["modules"]
    unicat.mutate = UnicatMutate(unicat)
    return unicat
