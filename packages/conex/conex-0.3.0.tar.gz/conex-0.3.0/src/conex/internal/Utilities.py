from ..commands.ConfigSubCommand import ConfigSubCommand
from conanapi import Reference


class Utilities:
    def __init__(self, conan, config: ConfigSubCommand):
        self._conan_inspect = conan.inspect
        self._conan_utilities = conan.utilities
        self._config = config

    def create_reference(self, path_to_conanfile):
        package_info = self._conan_inspect(path_to_conanfile, attributes=["name", "version"])

        name = package_info["name"]
        version = package_info["version"]
        user = self._config.get("user")
        channel = self._config.get("channel")

        return Reference(name, version, user, channel)

    def load_lockfile(self, file_path: str):
        return self._conan_utilities.load_lockfile(file_path)
