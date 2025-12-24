# settings

import os
import re
import socket
import subprocess
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import validate_call
from starlette.config import Config
from starlette.datastructures import Secret


class Get(Enum):
    OPTIONAL_READ_FILE = 1
    VALIDATE_PEM_CERTIFICATE_FILE = 2
    VALIDATE_PEM_PRIVATE_KEY_FILE = 3
    VALIDATE_PEM_PUBLIC_KEY_FILE = 4
    DECODE_SECRET = 5


default_webdriver_bin = subprocess.check_output("which geckodriver 2>/dev/null || true", shell=True, text=True).strip()
default_firefox_bin = subprocess.check_output("which firefox 2>/dev/null || true", shell=True, text=True).strip()

###############################################
#
#   Config file precedence: (dotenv format)
#
#    1 env var BCC_CONFIG_FILE
#    2 ./.bcc
#    3 $HOME/.config/bcc/config
#    4 /etc/bcc/config
#
###############################################

for CONFIG_FILE in [
    Path(os.environ.get("BCC_CONFIG_FILE", "")),
    Path(".bcc"),
    Path.home() / ".config" / "bcc" / "config",
    Path("/etc/bcc/config"),
]:
    if CONFIG_FILE.is_file():
        break
config = Config(CONFIG_FILE)

ADDRESS = config("ADDRESS", cast=str, default="127.0.0.1")
PORT = config("PORT", cast=int, default=8000)

ADMIN_USERNAME = config("ADMIN_USERNAME", cast=str, default="admin")
ADMIN_PASSWORD = config("ADMIN_PASSWORD", cast=Secret)
API_KEY = config("API_KEY", cast=Secret)
CALDAV_URL = config(
    "CALDAV_URL", cast=str, default="https://caldav." + ".".join(socket.getfqdn().split(".")[1:]) + "/baikal"
)
API_URL = config("API_URL", cast=str, default="https://caldav." + ".".join(socket.getfqdn().split(".")[1:]) + "/bcc")

CLIENT_CERT = config("CLIENT_CERT", cast=str, default=str(Path.home() / "certs" / "client.pem"))
CLIENT_KEY = config("CLIENT_KEY", cast=str, default=str(Path.home() / "certs" / "client.key"))

INSECURE_NO_CLIENT_CERT = config("INSECURE_NO_CLIENT_CERT", cast=bool, default=False)
INSECURE_NO_API_KEY = config("INSECURE_NO_API_KEY", cast=bool, default=False)

AUTO_LOGOUT_TIMER = config("AUTO_LOGOUT_TIMER", cast=int, default=5)
AUTO_SHUTDOWN_TIMER = config("AUTO_SHUTDOWN_TIMER", cast=int, default=30)

DEBUG = config("DEBUG", cast=bool, default=False)
LOG_LEVEL = config("LOG_LEVEL", cast=str, default="WARNING")
LOGGER_NAME = config("LOGGER_NAME", cast=str, default="bcc")
VERBOSE = config("VERBOSE", cast=bool, default=False)
DEBUG_LOG_HTML = config("DEBUG_LOG_HTML", cast=bool, default=False)
DEBUG_LOG_HEADERS = config("DEBUG_LOG_HEADERS", cast=bool, default=False)

PASSWD_FILE = config("PASSWD_FILE", cast=str, default=str(Path(CONFIG_FILE).parent / "passwd"))
PASSWD_MODE = config("PASSWD_MODE", cast=str, default="0660")


def dotenv(reveal_passwords=False):
    ret = ""
    sep = ""
    for key in sorted([k for k in globals().keys() if re.match("^[A-Z][A-Z_]*$", k)]):
        value = globals()[key]
        if isinstance(value, Secret):
            if reveal_passwords:
                value = str(value)
            else:
                value = "****************"
        if (not isinstance(value, str)) and str(value).isnumeric():
            value = str(value)
        if value is True:
            value = "1"
        elif value is False:
            value = "0"
        elif isinstance(value, str):
            if " " in value or "=" in value or '"' in value or "'" in value:
                value = "'" + value + "'"
        ret += f"{sep}{key}={value}"
        sep = "\n"
    return ret


def read_secret(value):
    if isinstance(value, Secret):
        value = str(value)
    if not value.startswith("@"):
        return value
    value = value[1:]
    if value.startswith("~"):
        path = Path.home()
        value = value[1:]
    else:
        path = Path(".")
    file = path / value
    value = file.read_text()
    value = value.strip()
    return value


def validate_pem_file(filename: str, pem_type: str):
    with Path(filename).open("r") as ifp:
        content = ifp.read()
        if "-----BEGIN" not in content or "-----END" not in content:
            raise ValueError(f"{filename} is not PEM format")
        if "cert" in pem_type:
            if not re.match(".*-----BEGIN CERTIFICATE-----.*", content, re.MULTILINE):
                raise ValueError(f"{filename} is not a certificate")
        elif "key" in pem_type:
            if "pub" in pem_type:
                if not re.match(".*-----BEGIN .*PUBLIC KEY-----.*", content, re.MULTILINE):
                    raise ValueError(f"{filename} is not a public key")
            elif "priv" in pem_type:
                if not re.match(".*-----BEGIN .*PRIVATE KEY-----.*", content, re.MULTILINE):
                    raise ValueError(f"{filename} is not a private key")
            else:
                if not re.match(".*-----BEGIN .* KEY-----.*", content, re.MULTILINE):
                    raise ValueError(f"{filename} is not a key")


@validate_call
def get(value: Any | None, name: str, *flags: Get) -> Any:
    """if value is None, set it from the named setting, performing post-processing if flags are set"""
    if value is None:
        value = globals()[name]
    for flag in flags:
        if flag == Get.DECODE_SECRET:
            if isinstance(value, Secret):
                value = str(value)
        elif flag == Get.OPTIONAL_READ_FILE:
            value = read_secret(value)
        elif flag == Get.VALIDATE_PEM_CERTIFICATE_FILE:
            validate_pem_file(value, "certificate")
        elif flag == Get.VALIDATE_PEM_PRIVATE_KEY_FILE:
            validate_pem_file(value, "privkey")
        elif flag == Get.VALIDATE_PEM_PUBLIC_KEY_FILE:
            validate_pem_file(value, "pubkey")
        else:
            raise ValueError(f"unrecognized settings flag: {flag}")
    return value
