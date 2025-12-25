from datetime import datetime


class UnicatModuleLog:
    def __init__(self, unicat, log):
        if not unicat._features.modules:
            raise NameError(
                f"name '{self.__class__.__name__}' is not defined (requires Unicat API version 2025.07.001)."
            )

        self._unicat = unicat
        self._data = log

    @property
    def timestamp(self):
        return datetime.fromtimestamp(self._data["timestamp"])

    @property
    def version(self):
        return self._data["version"]

    @property
    def action(self):
        return self._data["action"]

    @property
    def configuration(self):
        return self._data["configuration"]

    @property
    def command(self):
        return self._data["command"]

    @property
    def started_at(self):
        return datetime.fromtimestamp(self._data["started_at"])

    @property
    def ended_at(self):
        return datetime.fromtimestamp(self._data["ended_at"])

    @property
    def duration(self):
        return self._data["duration"]

    @property
    def status(self):
        return self._data["status"]

    @property
    def output(self):
        return self._data["output"]
