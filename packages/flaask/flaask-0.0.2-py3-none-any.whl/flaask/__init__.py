"""
⚠️  WARNING: You installed the wrong package! ⚠️

You probably meant to install 'flask':
    pip install flask

This package 'flaask' (typo) is a defensive registration
to protect users from typosquatting attacks.

To fix this:
    pip uninstall flaask
    pip install flask

The real Flask library: https://pypi.org/project/flask/
"""

import warnings
import sys

# Show warning immediately on import
warnings.warn(
    "\n\n"
    "⚠️  WRONG PACKAGE! You installed 'flaask' but probably meant 'flask'.\n"
    "   Run: pip uninstall flaask && pip install flask\n"
    "   Docs: https://pypi.org/project/flask/\n",
    UserWarning,
    stacklevel=2
)

# Also print to make sure they see it
print("""
╔══════════════════════════════════════════════════════════════════╗
║  ⚠️  TYPO DETECTED - WRONG PACKAGE INSTALLED                     ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  You installed:     flaask   (THIS PACKAGE - typo placeholder)   ║
║  You probably want: flask    (the actual web framework)          ║
║                                                                  ║
║  To fix:                                                         ║
║    pip uninstall flaask                                          ║
║    pip install flask                                             ║
║                                                                  ║
║  This package exists to protect you from typosquatting attacks.  ║
║  A malicious actor could have registered this name instead.      ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
""", file=sys.stderr)

__version__ = "0.0.2"
__author__ = "Security Researcher"

def __getattr__(name):
    raise ImportError(
        f"You imported 'flaask' but meant 'flask'. "
        f"Run: pip install flask"
    )
