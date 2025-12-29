# ⚠️ Wrong Package - You Probably Want `requests`

## You made a typo!

You installed:
```bash
pip install request  # ❌ This package (placeholder)
```

You probably meant:
```bash
pip install requests  # ✅ The actual HTTP library
```

## How to fix

```bash
pip uninstall request
pip install requests
```

## Why does this package exist?

This is a **defensive registration** against [typosquatting attacks](https://en.wikipedia.org/wiki/Typosquatting).

Typosquatting is when attackers register package names that are common misspellings of popular packages, then fill them with malware. When developers accidentally typo a package name, they install malware instead.

By registering this obvious typo (`request` without the 's'), we prevent malicious actors from using it to distribute malware.

### The real package

**requests** - Python HTTP for Humans™
- PyPI: https://pypi.org/project/requests/
- Docs: https://requests.readthedocs.io/
- GitHub: https://github.com/psf/requests

## Stats

The real `requests` package has **900+ million downloads per month**. Even a 0.01% typo rate would mean ~90,000 potential victims monthly.

## This package is safe

This package contains no malicious code. It only:
1. Prints a warning telling you about the typo
2. Raises helpful errors if you try to use it
3. Points you to the correct package

Stay safe out there! 🛡️

