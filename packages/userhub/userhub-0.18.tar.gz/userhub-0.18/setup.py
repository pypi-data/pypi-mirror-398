"""
Legacy setup.py shim for environments that still invoke setup.py directly.
Metadata and dependencies are kept in sync with pyproject.toml.
"""

import pathlib
import re

from setuptools import find_packages, setup


WORK_DIR = pathlib.Path(__file__).parent


def get_version():
    """Read the package version from userhub/__init__.py."""
    txt = (WORK_DIR / "userhub" / "__init__.py").read_text("utf-8")
    match = re.search(r'^__version__ = "([^"]+)"', txt, re.M)
    if not match:
        raise RuntimeError("Unable to determine version")
    return match.group(1)


setup(
    name="userhub",
    version=get_version(),
    description="User Authorization System",
    long_description=(WORK_DIR / "README.md").read_text("utf-8"),
    long_description_content_type="text/markdown",
    url="https://github.com/chilleco/userhub",
    author="Alex Poloz",
    author_email="alexypoloz@gmail.com",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Operating System :: OS Independent",
    ],
    keywords=(
        "auth, auth system, auth hub, user authenticator, authentication system"
    ),
    packages=find_packages(exclude=("tests",)),
    python_requires=">=3.8, <4",
    install_requires=[
        "libdev>=0.97",
        "consys>=0.44",
    ],
    extras_require={
        "dev": [
            "twine>=6.2.0",
            "setuptools>=80.9.0",
            "build>=1.2.1",
        ],
    },
    project_urls={
        "Homepage": "https://github.com/chilleco/userhub",
        "Source": "https://github.com/chilleco/userhub",
        "PyPI": "https://pypi.org/project/userhub/",
    },
    license="MIT",
    include_package_data=False,
)
