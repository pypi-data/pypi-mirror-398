from __future__ import annotations

from setuptools import find_packages, setup


def find_required():
    with open('requirements.txt') as f:
        return f.read().splitlines()


def find_dev_required():
    with open("requirements-dev.txt") as f:
        return f.read().splitlines()


setup(
    name="flake8-qa-style",
    version="1.0.2",
    description="flake8 based linter for e2e tests",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    python_requires=">=3.10",
    url="https://github.com/mytestopia/flake8-qa-style",
    author="Anna",
    author_email="testopia13@gmail.com",
    license="Apache-2.0",
    packages=find_packages(exclude=("tests",)),
    package_data={"flake8_qa_style": ["py.typed"]},
    install_requires=find_required(),
    tests_require=find_dev_required(),
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
