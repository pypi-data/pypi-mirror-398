from typing import Optional


class Reference:
    def __init__(self, name: str, version: str, user: Optional[str], channel: Optional[str]):
        self._name = name
        self._version = version
        self._user = user
        self._channel = channel

        if (self._user and not self._channel) or (not self._user and self._channel):
            raise ValueError()

    def __str__(self):
        if self._user:
            return f"{self._name}/{self._version}@{self._user}/{self._channel}"
        else:
            return f"{self._name}/{self._version}@"
