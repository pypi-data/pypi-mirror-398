import pytest

from unicat.module import UnicatModule
from unicat.module_action import UnicatModuleAction
from unicat.module_log import UnicatModuleLog
from unicat.mutate import UnicatMutate
from unicat.utils import MockFeatures


def test_module_classes(unicat):
    unicat._features = MockFeatures()
    with pytest.raises(NameError):
        UnicatModule(unicat, None)
    with pytest.raises(NameError):
        UnicatModuleAction(unicat, None)
    with pytest.raises(NameError):
        UnicatModuleLog(unicat, None)


def test_module_fetch(unicat):
    unicat._features = MockFeatures()
    unicat.mutate = UnicatMutate(unicat)
    with pytest.raises(AttributeError):
        unicat.get_all_module_names()
    with pytest.raises(AttributeError):
        unicat.get_module("Module 1")
    with pytest.raises(AttributeError):
        unicat.get_modules(["Module 1", "Module 2"])


def test_module_mutate(unicat):
    unicat._features = MockFeatures()
    unicat.mutate = UnicatMutate(unicat)
    with pytest.raises(AttributeError):
        unicat.mutate.register_module("Test Module", "0.0.1")
    with pytest.raises(AttributeError):
        unicat.mutate.unregister_module(None)
    with pytest.raises(AttributeError):
        unicat.mutate.set_module_key(None, None, None)
    with pytest.raises(AttributeError):
        unicat.mutate.set_module_keys(None, None)
    with pytest.raises(AttributeError):
        unicat.mutate.clear_module_key(None, None)
    with pytest.raises(AttributeError):
        unicat.mutate.clear_module_keys(None, None)
    with pytest.raises(AttributeError):
        unicat.mutate.publish_module_action(None, None, None)
    with pytest.raises(AttributeError):
        unicat.mutate.unpublish_module_action(None, None)
    with pytest.raises(AttributeError):
        unicat.mutate.add_module_log(None, None)
