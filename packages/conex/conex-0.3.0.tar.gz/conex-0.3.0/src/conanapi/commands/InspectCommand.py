from ..types.Reference import Reference
from typing import List, Union, Dict
import subprocess
import tempfile
import json
import os


class InspectCommand:
    def inspect(self, path_or_reference: Union[str, Reference], attributes: Union[str, List[str]] = None) -> Dict[str, str]:
        temp_json = None

        try:
            command = ["conan", "inspect"]
            if attributes:
                command += self._attributes(attributes)

            temp_json = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
            temp_json.close()

            command += ["--json", temp_json.name]

            if isinstance(path_or_reference, Reference):
                command.append(str(path_or_reference))
            elif isinstance(path_or_reference, str):
                command.append(path_or_reference)
            else:
                raise ValueError()

            subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            with open(temp_json.name) as jsonfile:
                return json.load(jsonfile)

        finally:
            if temp_json and os.path.exists(temp_json.name):
                os.unlink(temp_json.name)

    def _attributes(self, values: Union[str, List[str]]):
        params = []

        if isinstance(values, str):
            params += ["--attribute", values]
        elif isinstance(values, list):
            for value in values:
                params += self._attributes(value)
        else:
            print(type(values))
            raise ValueError()

        return params
