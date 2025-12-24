import json
import stat
from pathlib import Path

import pytest

from rstms_bcc import settings
from rstms_bcc.passwd import Accounts


def _chmod(file, mode):
    Path(file).chmod(int(mode, 8))


def _mode(file):
    mode = stat.S_IMODE(Path(file).stat().st_mode)
    return oct(mode)[2:].zfill(4)


def test_passwd_create(shared_datadir):
    file = shared_datadir / "passwd.bcc"
    assert file.is_file() is False
    settings.PASSWD_FILE = str(file)
    passwd = Accounts()
    assert passwd
    with pytest.raises(KeyError):
        passwd.get("howdy")
    assert file.is_file() is True
    assert _mode(file) == "0660"
    assert settings.PASSWD_MODE == "0660"


def test_passwd_exists(shared_datadir):
    file = shared_datadir / "passwd.bcc"
    file.write_text(json.dumps(dict(howdy="testvalue")))
    file.chmod(int("0600", 8))
    settings.PASSWD_FILE = str(file)
    settings.PASSWD_MODE = "0600"
    passwd = Accounts()
    assert passwd
    assert passwd.path == file
    assert passwd.read() == dict(howdy="testvalue")
    assert stat.S_IMODE(file.stat().st_mode) == int("0600", 8)
    assert passwd.get("howdy") == "testvalue"


def test_passwd_change(shared_datadir):
    file = shared_datadir / "passwd.bcc"
    file.write_text(json.dumps(dict(howdy="testvalue")))
    _chmod(file, "0664")
    assert _mode(file) == "0664"
    settings.PASSWD_FILE = str(file)
    settings.PASSWD_MODE = "0600"
    passwd = Accounts()
    assert passwd
    assert passwd.path == file
    assert _mode(file) == "0664"
    assert passwd.read() == dict(howdy="testvalue")
    assert _mode(file) == "0664"
    assert passwd.get("howdy") == "testvalue"
    passwd.set("howdy", "changedvalue")
    assert passwd.get("howdy") == "changedvalue"
    assert passwd.path == file
    assert _mode(file) == "0664"
