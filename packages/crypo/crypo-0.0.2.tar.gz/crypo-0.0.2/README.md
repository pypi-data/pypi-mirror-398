# ⚠️ Wrong Package - You Probably Want `pycryptodome` or `cryptography`

## You made a typo!

You installed:
```bash
pip install crypo  # ❌ This package (typo placeholder)
```

You probably meant:
```bash
pip install pycryptodome  # ✅ The actual crypto library
# or
pip install cryptography  # ✅ Another excellent option
```

## How to fix

```bash
pip uninstall crypo
pip install pycryptodome
```

## Why does this package exist?

This is a **defensive registration** against [typosquatting attacks](https://en.wikipedia.org/wiki/Typosquatting).

By registering this obvious typo (`crypo` missing the 't'), we prevent malicious actors from using it to distribute malware.

## Recommended crypto libraries

- **pycryptodome**: https://pypi.org/project/pycryptodome/
- **cryptography**: https://pypi.org/project/cryptography/

## This package is safe

This package contains no malicious code. It only prints a warning and points you to the correct packages.

Stay safe out there! 🛡️

