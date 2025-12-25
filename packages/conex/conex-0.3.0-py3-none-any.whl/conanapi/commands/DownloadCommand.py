import subprocess


class DownloadCommand:
    # noinspection PyMethodMayBeStatic
    def download(self, reference: str, remote: str = None, suppress_output: bool = False):

        command = ["conan", "download", reference]
        if remote is not None:
            command += ["--remote", remote]

        if suppress_output:
            subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.run(command)
