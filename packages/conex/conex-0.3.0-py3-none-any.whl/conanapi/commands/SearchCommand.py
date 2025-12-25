from pprint import pformat
import subprocess
import tempfile
import json
import os
import logging


class SearchCommand:
    def __init__(self):
        self._logger = logging.getLogger(__name__)

    # noinspection PyMethodMayBeStatic
    def search(self, pattern_or_reference: str, remote: str = None):
        temp_json = None

        try:
            command = ["conan", "search"]
            if remote is not None:
                command += ["--remote", remote]

            temp_json = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
            temp_json.close()

            command += ["--json", temp_json.name]
            command.append(pattern_or_reference)

            subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            with open(temp_json.name) as jsonfile:
                json_results = json.load(jsonfile)
                self._logger.debug(f"json output:\n{json.dumps(json_results, indent=4)}")

            error = json_results["error"]
            if error:
                self._logger.error("An unknown error occurred with conan search")
                raise Exception("Error occurred in search")

            packages = []
            results = json_results["results"]
            for result in results:
                items = result["items"]
                for item in items:
                    package = item["recipe"]["id"]
                    packages.append(package)

            self._logger.debug(f"packages:\n{pformat(packages)}")
            return packages

        finally:
            if temp_json and os.path.exists(temp_json.name):
                os.unlink(temp_json.name)
