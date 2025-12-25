from .commands.ConfigSubCommand import ConfigSubCommand
from .commands.EditableSubCommand import EditableSubCommand
from .commands.InspectCommand import InspectCommand
from .commands.UploadCommand import UploadCommand
from .commands.DownloadCommand import DownloadCommand
from .commands.SearchCommand import SearchCommand
from .internal.Utilities import Utilities


class ConanAPI:
    def __init__(self):
        self._utilities = Utilities()
        self._config = ConfigSubCommand()
        self._editable = EditableSubCommand()
        self._inspect = InspectCommand()
        self._upload = UploadCommand()
        self._download = DownloadCommand()
        self._search = SearchCommand()

    @property
    def utilities(self):
        return self._utilities

    @property
    def config(self):
        return self._config

    @property
    def editable(self):
        return self._editable

    @property
    def inspect(self):
        return self._inspect.inspect

    @property
    def upload(self):
        return self._upload.upload

    @property
    def download(self):
        return self._download.download

    @property
    def search(self):
        return self._search.search
