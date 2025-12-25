import os

from setuptools import find_packages, setup


def read_version():
    version_file = os.path.join(
        os.path.dirname(__file__), "treqs", "_version.py"
    )
    version_dict = {}
    with open(version_file, "r") as f:
        exec(f.read(), version_dict)
    return version_dict["__version__"]


def read_package_name():
    init_file = os.path.join(os.path.dirname(__file__), "treqs", "__init__.py")
    with open(init_file, "r") as f:
        for line in f:
            if line.startswith("__package_name__"):
                return line.split("=")[1].strip().strip('"').strip("'")
    raise ValueError("__package_name__ not found in __init__.py")


with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name=read_package_name(),
    version=read_version(),
    author="Eric Knauss",
    author_email="eric.knauss@cse.gu.se",
    description=(
        "Lightweight Git-native tool for managing requirements "
        "in agile projects."
    ),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitlab.com/treqs-on-git/treqs-ng",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Documentation",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
    python_requires=">=3.9",
    install_requires=[
        "click>=8.0",
        "lxml>=4.9.3",
        "pyyaml>=6.0",
    ],
    entry_points={
        "console_scripts": [
            "treqs=treqs.main:treqs",
        ],
    },
    extras_require={
        "dev": [
            "coverage",
            "coverage-badge",
            "ruff",
        ]
    },
)
