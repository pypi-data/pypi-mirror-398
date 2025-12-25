from typing import List
from ..internal import Utilities
import os


class UploadCommand:
    def __init__(self, conan, conex_utils: Utilities):
        self._conan_upload = conan.upload
        self._utils = conex_utils

    def upload(self, path_to_conanfile_or_lock: str, lockfile_only: bool = False, remote: str = None, upload_all: bool = True):
        conanfile_or_lockfile, is_lock_file = self._lookup_file(path_to_conanfile_or_lock, lockfile_only)

        if is_lock_file:
            lock_file = self._utils.load_lockfile(conanfile_or_lockfile)
            self._upload(lock_file.packages)

        else:
            reference = self._utils.create_reference(path_to_conanfile_or_lock)
            self._upload([str(reference)], remote, upload_all)

    def _upload(self, references: List[str], remote: str = None, upload_all: bool = True):
        for reference in references:
            self._conan_upload(reference, remote, upload_all)

    def _lookup_file(self, path_to_conanfile_or_lock: str, lockfile_only: bool):
        absolute_path = os.path.abspath(path_to_conanfile_or_lock)

        conanfile_path = None

        if not lockfile_only:
            conanfile_path = self._lookup_conanfile(absolute_path)

        if conanfile_path is not None:
            return conanfile_path, False

        lockfile_path = self._lookup_lockfile(absolute_path)
        if lockfile_path is None:
            raise ValueError()

        return lockfile_path, True

    # noinspection PyMethodMayBeStatic
    def _lookup_conanfile(self, absolute_path):
        conanfile_path = os.path.join(absolute_path, "conanfile.py")
        if os.path.exists(conanfile_path):
            return conanfile_path
        else:
            return None

    # noinspection PyMethodMayBeStatic
    def _lookup_lockfile(self, absolute_path):
        conanfile_path = os.path.join(absolute_path, "conan.lock")
        if os.path.exists(conanfile_path):
            return conanfile_path
        else:
            return None
