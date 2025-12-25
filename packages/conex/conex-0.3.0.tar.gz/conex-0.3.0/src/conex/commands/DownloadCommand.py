from ..internal import Utilities
from enum import Enum
import logging


class DownloadCommand:
    class InputType(Enum):
        PATTERN = 1,
        REFERENCE = 2

    def __init__(self, conan, conex_utils: Utilities):
        self._logger = logging.getLogger(__name__)

        self._conan = conan
        self._utils = conex_utils

    def download(self, pattern_or_reference: str, remote: str = None):
        self._download(pattern_or_reference, remote)

    def _download(self, pattern_or_reference: str, remote: str = None):
        input_type = self._get_input_type(pattern_or_reference)

        func = {
            DownloadCommand.InputType.PATTERN: self._download_from_pattern,
            DownloadCommand.InputType.REFERENCE: self._download_from_reference
        }

        # noinspection PyArgumentList
        return func[input_type](pattern_or_reference, remote)

    def _download_from_pattern(self, pattern: str, remote: str):
        pattern_results = self._conan.search(pattern, remote)
        for reference in pattern_results:
            self._download_from_reference(reference, remote)

        return pattern_results

    def _download_from_reference(self, reference: str, remote: str):
        self._conan.download(reference, remote)
        return [reference]

    @staticmethod
    def _get_input_type(pattern_or_reference: str):
        if "*" in pattern_or_reference:
            return DownloadCommand.InputType.PATTERN
        else:
            return DownloadCommand.InputType.REFERENCE
