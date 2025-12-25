import subprocess
import tempfile
import json
import os


class ConfigSubCommand:
    def __init__(self):
        pass

    # noinspection PyMethodMayBeStatic
    def home(self) -> str:
        temp_json = None

        try:
            temp_json = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
            temp_json.close()

            command = ["conan", "config", "home", "--json", temp_json.name]

            subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            with open(temp_json.name) as jsonfile:
                json_values = json.load(jsonfile)

            return json_values["home"]

        finally:
            if temp_json and os.path.exists(temp_json.name):
                os.unlink(temp_json.name)
