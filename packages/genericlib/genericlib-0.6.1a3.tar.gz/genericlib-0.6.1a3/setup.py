"""
setup.py for the genericlib package
===================================

This script defines the packaging configuration for the `genericlib` library,
enabling distribution via PyPI or installation in local environments. It uses
`setuptools` to specify metadata, dependencies, and packaging rules.

Overview
--------
- Package Name: `genericlib`
- Version: 0.6.0a0 (alpha release)
- License: BSD-3-Clause
- Author/Maintainer: Tuyen Mathew Duong
- Repository: https://github.com/Geeks-Trident-LLC/genericlib

Features
--------
- Provides reusable utilities for accelerating Python development, including
  support for regex generation and textfsm generation.
- Streamlines workflows by reducing redundancy and enabling efficient,
  adaptable, maintainable applications.

Configuration Details
---------------------
- Long description is loaded from `README.md` and rendered as Markdown.
- Dependencies: requires `pyyaml`.
- Packages: discovered automatically via `find_packages`, excluding common
  non-distribution directories (tests, examples, docs, build, dist, venv).
- Project URLs:
  - Documentation: GitHub Wiki
  - Source: GitHub repository
  - Issue Tracker: GitHub Issues
- Classifiers: specify development status, supported Python versions (3.9–3.12),
  operating systems (MacOS, Linux, Windows), intended audiences, and topics.

Usage
-----
This file is executed when installing the package via:

    pip install .

or when building distributions:

    python setup.py sdist bdist_wheel

It ensures that `genericlib` is packaged correctly with metadata, dependencies,
and resources included.
"""


from setuptools import setup, find_packages

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="genericlib",
    version="0.6.1a3",  # alpha versioning
    license="BSD-3-Clause",
    license_files=["LICENSE"],
    description="The Generic Python Library accelerates development with "
                "reusable utilities, supporting regexapp and "
                "textfsmgen while streamlining workflows, "
                "reducing redundancy, and enabling efficient, adaptable, "
                "maintainable applications.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Tuyen Mathew Duong",
    author_email="tuyen@geekstrident.com",
    maintainer="Tuyen Mathew Duong",
    maintainer_email="tuyen@geekstrident.com",
    install_requires=[
        "pyyaml",
    ],
    url="https://github.com/Geeks-Trident-LLC/genericlib",
    packages=find_packages(
        exclude=(
            "tests*", "testing*", "examples*",
            "build*", "dist*", "docs*", "venv*"
        )
    ),
    project_urls={
        "Documentation": "https://github.com/Geeks-Trident-LLC/genericlib/wiki",
        "Source": "https://github.com/Geeks-Trident-LLC/genericlib",
        "Tracker": "https://github.com/Geeks-Trident-LLC/genericlib/issues",
    },
    python_requires=">=3.9",
    include_package_data=True,
    package_data={"": ["LICENSE", "README.md"]},
    classifiers=[
        # development status
        "Development Status :: 3 - Alpha",
        # natural language
        "Natural Language :: English",
        # intended audience
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Manufacturing",
        "Intended Audience :: Other Audience",
        "Intended Audience :: Science/Research",
        # operating system
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX :: Linux",
        "Operating System :: Microsoft :: Windows",
        # programming language
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        # topic
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Software Development :: Testing",
        "Topic :: Scientific/Engineering",
        "Topic :: Text Processing",
    ],
)
