"""
⚠️  WARNING: You installed the wrong package! ⚠️

You probably meant to install 'crypto' or 'pycryptodome':
    pip install pycryptodome

This package 'crypo' (typo) is a defensive registration
to protect users from typosquatting attacks.

To fix this:
    pip uninstall crypo
    pip install pycryptodome

Recommended crypto libraries:
- pycryptodome: https://pypi.org/project/pycryptodome/
- cryptography: https://pypi.org/project/cryptography/
"""

import warnings
import sys

# Show warning immediately on import
warnings.warn(
    "\n\n"
    "⚠️  WRONG PACKAGE! You installed 'crypo' but probably meant 'crypto' or 'pycryptodome'.\n"
    "   Run: pip uninstall crypo && pip install pycryptodome\n"
    "   Or:  pip uninstall crypo && pip install cryptography\n",
    UserWarning,
    stacklevel=2
)

# Also print to make sure they see it
print("""
╔══════════════════════════════════════════════════════════════════╗
║  ⚠️  TYPO DETECTED - WRONG PACKAGE INSTALLED                     ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  You installed:     crypo         (THIS PACKAGE - typo only)     ║
║  You probably want: pycryptodome  (the actual crypto library)    ║
║                 or: cryptography  (another great option)         ║
║                                                                  ║
║  To fix:                                                         ║
║    pip uninstall crypo                                           ║
║    pip install pycryptodome                                      ║
║                                                                  ║
║  This package exists to protect you from typosquatting attacks.  ║
║  A malicious actor could have registered this name instead.      ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
""", file=sys.stderr)

__version__ = "0.0.1"
__author__ = "Security Researcher"

def __getattr__(name):
    raise ImportError(
        f"You imported 'crypo' but meant 'crypto' or 'pycryptodome'. "
        f"Run: pip install pycryptodome"
    )

