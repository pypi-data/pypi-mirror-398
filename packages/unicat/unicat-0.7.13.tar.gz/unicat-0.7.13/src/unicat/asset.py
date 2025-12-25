class UnicatAsset:
    def __init__(self, unicat, gid):
        self._unicat = unicat
        self._data = self._unicat.assets[gid]

    @property
    def gid(self):
        return self._data["gid"]

    @property
    def pathname(self):
        return self._data["pathname"]

    @property
    def path(self):
        return self._data["path"]

    @property
    def name(self):
        return self._data["name"]

    @property
    def is_file(self):
        return self._data["is_file"]

    @property
    def type(self):
        return self._data["type"]

    @property
    def childcount(self):
        return self._data["childcount"]

    @property
    def status(self):
        return self._data["status"]

    @property
    def is_deleted(self):
        return self._data["status"] == "deleted"

    @property
    def info(self):
        return self._data["info"]

    @property
    def transforms(self):
        return self._data["transforms"]

    @property
    def default_transform(self):
        if self._data["transforms"] is None:
            return None
        return self._data["transforms"].get("_main_", None)

    @property
    def title(self):
        return self._data["title"]

    @property
    def description(self):
        return self._data["description"]

    @property
    def created_on(self):
        return self._data["created_on"]

    @property
    def updated_on(self):
        return self._data["updated_on"]

    def publish(self):
        if not self.is_file:
            return None
        public_url = self._unicat.publish_asset(self)
        return public_url

    def publish_transformed(self, transform=None):
        if not self.is_file:
            return None
        public_url = self._unicat.publish_transformed_asset(self, transform=transform)
        return public_url

    def download(self, pathname=None):
        if not self.is_file:
            return None
        pathname = self._unicat.download_asset(
            self, pathname=pathname, updated_on=self.updated_on
        )
        return pathname

    def download_transformed(self, transform=None, pathname=None):
        if not self.is_file:
            return None
        pathname = self._unicat.download_transformed_asset(
            self, transform=transform, pathname=pathname, updated_on=self.updated_on
        )
        return pathname
