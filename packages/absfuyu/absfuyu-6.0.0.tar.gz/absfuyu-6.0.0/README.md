<div align="center">
    <h1 align="center">
        <img src="https://github.com/AbsoluteWinter/AbsoluteWinter.github.io/blob/main/absfuyu/images/repository-image-crop.png?raw=true" alt="absfuyu"/>
    </h1>
    <p align="center">
        <a href="https://pypi.org/project/absfuyu/"><img src="https://img.shields.io/pypi/pyversions/absfuyu?style=flat-square&logo=python" alt="PyPI Supported Versions"/></a>
        <a href="https://pypi.org/project/absfuyu/"><img src="https://img.shields.io/pypi/dm/absfuyu?style=flat-square&color=blue" alt="PyPI Downloads"/></a>
        <a href="https://pypi.org/project/absfuyu/"><img src="https://img.shields.io/pypi/v/absfuyu?style=flat-square&logo=pypi" /></a>
        <a><img src="https://img.shields.io/pypi/l/absfuyu?style=flat-square&logo=github&color=blue"/></a>
        <a><img src="https://img.shields.io/badge/code%20style-black-black?style=flat-square"/></a>
        <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json&style=flat-square" alt="Ruff" style="max-width:100%;"></a>
    </p>
</div>

---

## **SUMMARY:**

This project is a collection of code primarily developed as a personal hobby. It aims to provide practical experience and enhance my coding skills while exploring potential future applications.

## **INSTALLATION:**

To install the package, run the following command:

```bash
pip install -U absfuyu
```

## **USAGE:**

```python
import absfuyu
help(absfuyu)
```

### Notable features

**absfuyu.core**: Provides base components for additional functionalities.

```python
# Decorators that adds info to __doc__
from absfuyu.core.docstring import versionadded, versionchanged, deprecated

# Class mixins for enhanced functionality
from absfuyu.core.baseclass import AutoREPRMixin, GetClassMembersMixin
```

**absfuyu.dxt**: Extension for `list`, `str`, `dict`, `int`.

```python
from absfuyu.dxt import DictExt, IntExt, ListExt, Text
for x in [DictExt, IntExt, ListExt, Text]:
    x.show_all_methods(print_result=1)
```

**absfuyu.tools.Inspector**: An object inspector

```python
from absfuyu.tools import Inspector
print(Inspector(Inspector))
```

There are many additional features available to explore.

## **DOCUMENTATION:**

For more detailed information about the project, please refer to the documentation available at the following link:

> [Project Documentation](https://absolutewinter.github.io/absfuyu-docs/)

## **DEVELOPMENT SETUP**

1. Create a Virtual Environment

```bash
python -m venv env
```

Note: You may need to execute this command in PowerShell on Windows:

```powershell
Set-ExecutionPolicy -ExecutionPolicy Unrestricted -Scope CurrentUser
```

2. Install Required Packages

```bash
python -m pip install -e .[full,dev]
```

3. Acquire Information About the Development Environment Configuration

```bash
hatch env show
```

## **LICENSE:**

This project is licensed under the MIT License.
