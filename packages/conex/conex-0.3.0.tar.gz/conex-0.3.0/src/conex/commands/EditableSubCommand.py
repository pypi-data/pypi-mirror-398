from .ConfigSubCommand import ConfigSubCommand
from ..internal.Utilities import Utilities
import re


class EditableSubCommand:
    def __init__(self, conan, utils: Utilities, config: ConfigSubCommand):
        self._conan_editable = conan.editable
        self._utils = utils
        self._config = config

    def add(self, path_to_conanfile, path_to_layout=None):
        reference = self._utils.create_reference(path_to_conanfile)
        self._conan_editable.add(path_to_conanfile, reference, path_to_layout)

    def remove(self, path_to_conanfile, remove_all):
        if remove_all is not None:
            self._remove_all()
        elif path_to_conanfile is not None:
            self._remove_package(path_to_conanfile)
        else:
            raise ValueError('Unsupported operation')

    def _remove_package(self, path_to_conanfile):
        reference = self._utils.create_reference(path_to_conanfile)
        self._conan_editable.remove(reference)

    def _remove_all(self):
        output = self._conan_editable.list()
        if not output:
            print("No editable packages found. Nothing to do.")
            return

        # Use regex to find the package names (the first line of each 3-line block)
        # Based on the sample, items look like 'name/version@user/channel'
        # We look for lines that don't start with 'Path:' or 'Layout:'
        references = re.findall(r'^(\S+/\S+@\S+/\S+)', output, re.MULTILINE)
        if not references:
            print("No editable packages identified in the output.")
            return

        print(f"Found {len(references)} editable packages:")
        for reference in references:
            print(f"  - {reference}")

        print()

        for reference in references:
            self._conan_editable.remove(reference)
