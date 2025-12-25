from .DownloadCommand import DownloadCommand
from .UploadCommand import UploadCommand
import logging


class MigrateCommand:
    def __init__(self, download: DownloadCommand, upload: UploadCommand):
        self._logger = logging.getLogger(__name__)

        self._download = download
        self._upload = upload

    # noinspection PyProtectedMember
    def migrate(self, pattern_or_reference: str, source: str, destination: str):
        download_packages = self._download._download(pattern_or_reference, source)
        self._upload._upload(download_packages, destination, True)
