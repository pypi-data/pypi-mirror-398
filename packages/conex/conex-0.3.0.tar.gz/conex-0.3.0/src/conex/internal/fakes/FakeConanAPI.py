from typing import Optional, Union, List, Dict
from conanapi import Reference, LockFile


class _FakeUtilities:
    def __init__(self):
        self.lockfile_packages = []

    def load_lockfile(self, file_path: str):
        lock_file = LockFile()
        lock_file._packages = self.lockfile_packages
        return lock_file


class _FakeConfigCommand:
    def __init__(self):
        self._home = None

    def set_home(self, file_path):
        self._home = file_path

    def home(self) -> str:
        return self._home


class _FakeEditableCommand:
    def __init__(self):
        self._editables = {}

    @property
    def editables(self):
        return self._editables

    def is_editable(self, reference: Union[str, Reference]):
        return reference in self._editables

    def add(self, path: str, reference: Union[str, Reference], layout: Optional[str] = None):
        item = {
            "path": path,
            "reference": str(reference),
            "layout": layout
        }
        self._editables[item["reference"]] = item

    def remove(self, reference: Union[str, Reference]):
        self._editables.pop(str(reference))

    def list(self):
        output = ""
        for item in self._editables.values():
            output += f"{item['reference']}\n"
            output += f"    Path: {item['path']}\n"
            output += f"    Layout: {item['layout']}\n"
        return output


class _FakeInspectCommand:
    def __init__(self):
        self.attributes = {}

    def inspect(self, path_or_reference: Union[str, Reference], attributes: Union[str, List[str]] = None) -> Dict[str, str]:
        return self.attributes


class _FakeUploadCommand:
    def __init__(self):
        self.uploads = []

    def upload(self, pattern_or_reference: str, remote: str = None, upload_all: bool = False):
        item = {
            "pattern_or_reference": pattern_or_reference,
            "remote": remote,
            "upload_all": upload_all
        }

        self.uploads.append(item)


class FakeConanAPI:
    def __init__(self):
        self._utilities = _FakeUtilities()
        self._config = _FakeConfigCommand()
        self._editable = _FakeEditableCommand()
        self._inspect = _FakeInspectCommand()
        self._upload = _FakeUploadCommand()

    @property
    def fake_utilities(self):
        return self._utilities

    @property
    def fake_config(self):
        return self._config

    @property
    def fake_editable(self):
        return self._editable

    @property
    def fake_inspect(self):
        return self._inspect

    @property
    def fake_upload(self):
        return self._upload

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
