class UnicatModuleAction:
    def __init__(self, unicat, action):
        if not unicat._features.modules:
            raise NameError(
                f"name '{self.__class__.__name__}' is not defined (requires Unicat API version 2025.07.001)."
            )

        self._unicat = unicat
        self._data = action

    @property
    def name(self):
        return self._data["name"]

    @property
    def configuration(self):
        return self._data["configuration"]
