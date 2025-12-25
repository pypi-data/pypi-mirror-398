from .module_action import UnicatModuleAction
from .module_log import UnicatModuleLog


class UnicatModule:
    def __init__(self, unicat, name):
        if not unicat._features.modules:
            raise NameError(
                f"name '{self.__class__.__name__}' is not defined (requires Unicat API version 2025.07.001)."
            )

        self._unicat = unicat
        self._data = self._unicat.modules[name]

    @property
    def name(self):
        return self._data["name"]

    @property
    def version(self):
        return self._data["version"]

    @property
    def keys(self):
        return self._data["keys"]

    @property
    def actions(self):
        return {
            name: UnicatModuleAction(self._unicat, configuration)
            for name, configuration in self._data["actions"].items()
        }

    @property
    def logs(self):
        return [UnicatModuleLog(self._unicat, log) for log in self._data["logs"]]
