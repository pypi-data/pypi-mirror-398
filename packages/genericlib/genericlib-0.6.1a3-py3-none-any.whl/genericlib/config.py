"""
genericlib.config
=================

Package metadata and configuration attributes.

This module centralizes versioning information for the `genericlib` package,
providing a single source of truth for the current release version. By exposing
the `version` attribute, it ensures consistency across the package when reporting,
logging, or displaying edition details.

Attributes
----------
__version__ : str
    Internal representation of the current package version.
version : str
    Publicly exported version string, identical to `__version__`.

Public API
----------
- `version`: The current release version of the `genericlib` package.

Use Cases
---------
- Displaying the package version in application logs or CLI tools.
- Ensuring consistent version reporting across modules.
- Facilitating automated checks for compatibility or upgrades.
"""

__version__ = '0.6.1a3'
version = __version__

__all__ = [
    'version'
]
