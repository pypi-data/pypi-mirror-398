# jupyterlab_fold_all_code_extension

[![GitHub Actions](https://github.com/stellarshenson/jupyterlab_fold_all_code_extension/actions/workflows/build.yml/badge.svg)](https://github.com/stellarshenson/jupyterlab_fold_all_code_extension/actions/workflows/build.yml)
[![npm version](https://img.shields.io/npm/v/jupyterlab_fold_all_code_extension.svg)](https://www.npmjs.com/package/jupyterlab_fold_all_code_extension)
[![PyPI version](https://img.shields.io/pypi/v/jupyterlab-fold-all-code-extension.svg)](https://pypi.org/project/jupyterlab-fold-all-code-extension/)
[![Total PyPI downloads](https://static.pepy.tech/badge/jupyterlab-fold-all-code-extension)](https://pepy.tech/project/jupyterlab-fold-all-code-extension)
[![JupyterLab 4](https://img.shields.io/badge/JupyterLab-4-orange.svg)](https://jupyterlab.readthedocs.io/en/stable/)
[![Brought To You By KOLOMOLO](https://img.shields.io/badge/Brought%20To%20You%20By-KOLOMOLO-00ffff?style=flat)](https://kolomolo.com)

Export notebooks with folded code cells hidden. Perfect for sharing clean notebooks with non-technical audiences - fold code, save, and export to HTML or PDF without visible code.

## Features

- **Export with Hidden Code** - Folded code cells are automatically hidden when exporting to HTML, PDF, and other formats
- **Fold/Expand All** - Commands available in the View menu to fold or expand all code cells at once

> [!IMPORTANT]
> To export a notebook with folded code cells hidden, you must **save the notebook first**. The export reads the saved file, so unsaved changes will not be reflected in the exported document.

## Installation

Requires JupyterLab 4.0.0 or higher.

```bash
pip install jupyterlab_fold_all_code_extension
```

## Uninstall

```bash
pip uninstall jupyterlab_fold_all_code_extension
```
