from typing import List, Type, TypeVar
import json


T = TypeVar('T', bound='LockFile')


class LockFile:
    @classmethod
    def load(cls: Type[T], file_path: str) -> T:
        with open(file_path, "r") as file:
            json_lock = json.load(file)

        LockFile._check_version(json_lock)

        lock_file = LockFile()
        lock_file._packages = LockFile._get_packages(json_lock)
        return lock_file

    def __init__(self):
        self._packages = []

    @property
    def packages(self) -> List[str]:
        return self._packages

    @staticmethod
    def _check_version(json_lock):
        version = json_lock["version"]
        if version != "0.4":
            raise ImportError(
                "ERROR: conan.lock version {} is not supported".format(version)
            )

    @staticmethod
    def _get_packages(json_lock):
        json_nodes = json_lock["graph_lock"]["nodes"]

        requires = set()
        package_dict = {}

        i = 0
        json_node = LockFile._get_node_by_index(json_nodes, i)
        while json_node is not None:

            # first node is root node
            if i != 0 and "ref" in json_node:
                ref = json_node["ref"]
                prev = json_node["prev"]
                package_id = json_node["package_id"]

                package_reference = "{}:{}#{}".format(ref, package_id, prev)
                package_dict[str(i)] = package_reference

            if "requires" in json_node:
                requires |= set(json_node["requires"])

            i += 1
            json_node = LockFile._get_node_by_index(json_nodes, i)

        packages = []
        for i in requires:
            packages.append(package_dict[i])

        return packages

    @staticmethod
    def _get_node_by_index(json_nodes, index):
        try:
            return json_nodes[str(index)]
        except KeyError:
            return None
