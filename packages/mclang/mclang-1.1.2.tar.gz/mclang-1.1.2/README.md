# mclang

![Tests](https://github.com/legopitstop/mclang/actions/workflows/tests.yml/badge.svg)
[![PyPI](https://img.shields.io/pypi/v/mclang)](https://pypi.org/project/mclang/)
[![Python](https://img.shields.io/pypi/pyversions/mclang)](https://www.python.org/downloads//)
![Downloads](https://img.shields.io/pypi/dm/mclang)
![Status](https://img.shields.io/pypi/status/mclang)
[![Issues](https://img.shields.io/github/issues/legopitstop/mclang)](https://github.com/legopitstop/mclang/issues)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

Create or open Minecraft: Bedrock Edition `.lang` files.

## Installation

Install the module with pip:

```bat
pip3 install mclang
```

Update existing installation: `pip3 install mclang --upgrade`

## Links

- [Documentation](https://docs.lpsmods.dev/mclang)
- [Source Code](https://github.com/legopitstop/mclang)

## Features

- Read and write to `.lang` files.
- Supports comments
- Add translation support to your Python application.
- Translate your .lang file between different languages.

## Example

```Python
lang = """
test=This is cool!
test2=It worked!
"""

doc = mclang.loads(lang)
print(doc.tl("test"))
# This is cool!
```
