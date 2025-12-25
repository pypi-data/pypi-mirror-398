class UnicatError(Exception):
    def __init__(self, message: str, error_result: dict):
        if not isinstance(error_result, dict):
            raise TypeError("error_result must be a Unicat error result dict")
        super().__init__(message, error_result)

    @property
    def code(self):
        return self.args[1].get("code", None)

    @property
    def message(self):
        return self.args[1].get("message", None)

    @property
    def info(self):
        return self.args[1].get("info", None)

    def __str__(self):
        return self.args[0]
