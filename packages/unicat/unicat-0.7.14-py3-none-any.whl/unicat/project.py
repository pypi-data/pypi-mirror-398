class UnicatProject:
    def __init__(self, unicat, gid):
        self._unicat = unicat
        self._data = self._unicat.projects[gid]

    @property
    def gid(self):
        return self._data["gid"]

    @property
    def name(self):
        return self._data["name"]

    @property
    def owner(self):
        from .user import UnicatUser

        return UnicatUser(self._unicat, self._data["owner"])

    @property
    def icon(self):
        return self._data["icon"]

    @property
    def status(self):
        return self._data["status"]

    @property
    def languages(self):
        return self._data["options"]["languages"]

    @property
    def default_language(self):
        return self._data["options"]["languages"][0]

    @property
    def channels(self):
        return {
            self._data["options"]["channels"][key]: key
            for key in self._data["options"]["orderedchannels"]
        }

    @property
    def default_channel(self):
        return (
            self._data["options"]["orderedchannels"][1]
            if len(self._data["options"]["orderedchannels"]) > 1
            else None
        )

    def channel_name(self, key):
        return self._data["options"]["channels"][key]

    @property
    def orderings(self):
        return {
            self._data["options"]["orderings"][key]: key
            for key in self._data["options"]["orderedorderings"]
        }

    @property
    def default_ordering(self):
        return self._data["options"]["orderedorderings"][0]

    def ordering_name(self, key):
        return self._data["options"]["orderings"][key]

    @property
    def fieldlists(self):
        return {
            self._data["options"]["fieldlists"][key]: key
            for key in self._data["options"]["orderedfieldlists"]
        }

    @property
    def default_fieldlist(self):
        return self._data["options"]["orderedfieldlists"][0]

    def fieldlist_name(self, key):
        return self._data["options"]["fieldlists"][key]

    @property
    def backups(self):
        from .projectbackup import UnicatProjectBackup

        return [
            UnicatProjectBackup(self._unicat, self.gid, backup_version)
            for backup_version in self._data["backups"]["versions"]
            if backup_version["version"] != 0
        ]

    def get_backup(self, version):
        backups = [backup for backup in self.backups if backup.version == version]
        return backups[0] if len(backups) else None

    @property
    def members(self):
        from .projectmember import UnicatProjectMember

        return [
            UnicatProjectMember(self._unicat, project_member)
            for project_member in self._unicat.projects_members.values()
            if project_member["project_gid"] == self.gid
        ]
