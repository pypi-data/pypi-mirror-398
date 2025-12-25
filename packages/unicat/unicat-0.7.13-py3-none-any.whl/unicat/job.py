# from .project import UnicatProject


class UnicatJob:
    def __init__(self, unicat, cursor, gid, return_value):
        self._unicat = unicat
        self._cursor = cursor
        self._gid = gid
        self._progress = {}
        self._return_value = return_value

    @property
    def gid(self):
        return self._gid

    @property
    def name(self):
        if "job" not in self._progress:
            return "unknown"
        return self._progress["job"]

    @property
    def status(self):
        if "status" not in self._progress:
            return "untracked"
        return self._progress["status"]

    @property
    def info(self):
        if "info" not in self._progress:
            return {}
        return self._progress["info"]

    @property
    def created_on(self):
        if "created_on" not in self._progress:
            return None
        return self._progress["created_on"]

    @property
    def updated_on(self):
        if "updated_on" not in self._progress:
            return None
        return self._progress["updated_on"]

    @property
    def progress(self):
        return {
            "gid": self.gid,
            "name": self.name,
            "status": self.status,
            "info": self.info,
            "created_on": self.created_on,
            "updated_on": self.updated_on,
        }

    @property
    def return_value(self):
        return self._return_value

    def track(self, timeout_in_seconds=None, poll_interval_in_seconds=1.0):
        for progress in self._unicat.api.track_job(
            self._cursor,
            self._gid,
            timeout_in_seconds=timeout_in_seconds,
            poll_interval_in_seconds=poll_interval_in_seconds,
        ):
            self._progress = progress
            yield self.status
