# jupyterlab_file_browser_sorting_extension

[![GitHub Actions](https://github.com/stellarshenson/jupyterlab_file_browser_sorting_extension/actions/workflows/build.yml/badge.svg)](https://github.com/stellarshenson/jupyterlab_file_browser_sorting_extension/actions/workflows/build.yml)
[![npm version](https://img.shields.io/npm/v/jupyterlab_file_browser_sorting_extension.svg)](https://www.npmjs.com/package/jupyterlab_file_browser_sorting_extension)
[![PyPI version](https://img.shields.io/pypi/v/jupyterlab-file-browser-sorting-extension.svg)](https://pypi.org/project/jupyterlab-file-browser-sorting-extension/)
[![Total PyPI downloads](https://static.pepy.tech/badge/jupyterlab-file-browser-sorting-extension)](https://pepy.tech/project/jupyterlab-file-browser-sorting-extension)
[![JupyterLab 4](https://img.shields.io/badge/JupyterLab-4-orange.svg)](https://jupyterlab.readthedocs.io/en/stable/)
[![Brought To You By KOLOMOLO](https://img.shields.io/badge/Brought%20To%20You%20By-KOLOMOLO-00ffff?style=flat)](https://kolomolo.com)

JupyterLab extension that implements LC_COLLATE=C (ASCIIbetical) sorting for the file browser.

## Features

- **LC_COLLATE=C sorting** - Standard Unix sorting order used by `ls` with C locale
- **Dot files first** - Hidden files (starting with `.`) appear before other files
- **Uppercase before lowercase** - Capital letters (A-Z) sort before lowercase (a-z)
- **ASCII order** - Characters sorted by their ASCII code values
- **Toggle via context menu** - Right-click in the file browser to enable/disable

## Usage

Right-click anywhere in the file browser content area and select **"Use Unix-Style Sorting (LC_COLLATE=C)"** to toggle the sorting mode. The setting is persisted across sessions.

When enabled, the extension sorts files using the standard Unix C locale collation sequence:

```
. (dot) -> 0-9 -> A-Z -> _ (underscore) -> a-z
```

**Example sort order:**

```
.hidden
.profile
123file
ABC
Makefile
README
_config
abc
readme
zebra
```

This matches the behavior of `LC_COLLATE=C ls` on Unix systems.

## Requirements

- JupyterLab >= 4.0.0

## Installation

```bash
pip install jupyterlab_file_browser_sorting_extension
```

## Uninstall

```bash
pip uninstall jupyterlab_file_browser_sorting_extension
```
