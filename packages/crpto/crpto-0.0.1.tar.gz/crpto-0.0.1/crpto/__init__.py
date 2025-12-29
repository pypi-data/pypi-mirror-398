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

__version__ = "0.0.1"

def __getattr__(name):
    raise ImportError(
        "For cryptography, use 'pycryptodome' or 'cryptography'. "
        "Run: pip install pycryptodome"
    )

