import subprocess


class UploadCommand:
    # noinspection PyMethodMayBeStatic
    def upload(self, pattern_or_reference: str, remote: str = None, upload_all: bool = False, suppress_output: bool = False):
        command = ["conan", "upload", pattern_or_reference]
        if remote is not None:
            command += ["--remote", remote]

        if upload_all:
            command += ["--all"]

        if suppress_output:
            subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.run(command)
