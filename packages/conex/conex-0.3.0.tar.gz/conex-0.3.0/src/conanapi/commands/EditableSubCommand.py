from typing import Optional, Union
from ..types.Reference import Reference
import subprocess


class EditableSubCommand:

    # noinspection PyMethodMayBeStatic
    def add(self, path: str, reference: Union[str, Reference], layout: Optional[str] = None) -> int:
        if isinstance(reference, Reference):
            reference = str(reference)

        command = ["conan", "editable", "add", path, reference]
        if layout:
            command += ["-l", layout]

        result = subprocess.run(command)
        return result.returncode

    # noinspection PyMethodMayBeStatic
    def remove(self, reference: Union[str, Reference]) -> int:
        if isinstance(reference, Reference):
            reference = str(reference)

        command = ["conan", "editable", "remove", reference]
        result = subprocess.run(command)
        return result.returncode

    def list(self) -> str:
        command = ["conan", "editable", "list"]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return result.stdout.strip()
