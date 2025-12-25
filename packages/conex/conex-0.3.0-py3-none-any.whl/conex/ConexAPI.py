from .commands.ConfigSubCommand import ConfigSubCommand
from .commands.EditableSubCommand import EditableSubCommand
from .commands.UploadCommand import UploadCommand
from .commands.DownloadCommand import DownloadCommand
from .commands.MigrateCommand import MigrateCommand
from .internal.Utilities import Utilities
from conanapi import ConanAPI


class ConexAPI:
    config_filename = "conex.toml"

    def __init__(self, conan=ConanAPI()):
        self._config = ConfigSubCommand(conan, ConexAPI.config_filename)
        self._utils = Utilities(conan, self._config)
        self._editable = EditableSubCommand(conan, self._utils, self._config)
        self._upload = UploadCommand(conan, self._utils)
        self._download = DownloadCommand(conan, self._utils)
        self._migrate = MigrateCommand(self._download, self._upload)

    @property
    def config(self):
        return self._config

    @property
    def editable(self):
        return self._editable

    @property
    def upload(self):
        return self._upload.upload

    @property
    def download(self):
        return self._download.download

    @property
    def migrate(self):
        return self._migrate.migrate
