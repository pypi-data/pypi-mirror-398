import json
from pathlib import Path

from . import settings


class AccountException(Exception):
    pass


class AccountNotFound(AccountException):
    pass


class Accounts:
    def __init__(self, filename=None):
        if not filename:
            filename = settings.PASSWD_FILE
        try:
            self.path = Path(filename)
            if not self.path.is_file():
                self.write(dict())
                mode = int(settings.PASSWD_MODE, 8)
                self.path.chmod(mode)
        except Exception as e:
            raise AccountException({e.__class__.__name__: str(e)}) from e

    def read(self):
        try:
            return json.loads(self.path.read_text())
        except Exception as e:
            raise AccountException({e.__class__.__name__: str(e)}) from e

    def write(self, values):
        try:
            with self.path.open("w+") as fp:
                fp.write(json.dumps(values, indent=2) + "\n")
        except Exception as e:
            raise AccountException({e.__class__.__name__: str(e)}) from e
        return self.read()

    def get(self, username):
        values = self.read()
        if username in values:
            return values[username]
        raise AccountNotFound(f"{username=}")

    def set(self, username, password):
        values = self.remove(username)
        values[username] = password
        return self.write(values)

    def remove(self, username):
        values = self.read()
        while values.pop(username, None):
            pass
        return self.write(values)
