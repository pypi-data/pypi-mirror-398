from ..types.LockFile import LockFile


class Utilities:

    # noinspection PyMethodMayBeStatic
    def load_lockfile(self, file_path: str):
        return LockFile.load(file_path)
