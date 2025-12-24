# TripleP - PPP - PyProject Parser

![PyPI - License](https://img.shields.io/pypi/l/triplep?style=for-the-badge)
![PyPI - Types](https://img.shields.io/pypi/types/triplep?style=for-the-badge)
![PyPI - Version](https://img.shields.io/pypi/v/triplep?style=for-the-badge)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/triplep?style=for-the-badge)

TripleP - PPP - PyProject Parser is a lightweight Python utility that enables effortless access to your project's metadata directly from pyproject.toml at runtime.

## Installation

`pip install triplep`

## Features

- Automatic `pyproject.toml` file discovery
- Parsing metadata into dataclass objects
- Raw access when required
- Fully typed

## Limitations

- Basic support for dataclass parsing of `[project]` block
- Sync only
