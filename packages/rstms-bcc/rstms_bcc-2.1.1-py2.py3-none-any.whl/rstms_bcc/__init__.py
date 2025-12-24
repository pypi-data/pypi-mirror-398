"""Top-level package for bcc."""

import sys
import warnings

if sys.platform.startswith("openbsd"):
    # suppress urllib3 complaint about libreSSL on OpenBSD
    warnings.filterwarnings("ignore", message="urllib3 v2 only supports OpenSSL")

from .app import app
from .cli import bcc
from .version import __author__, __email__, __timestamp__, __version__

__all__ = ["app", "bcc", "__version__", "__timestamp__", "__author__", "__email__"]
