try:
    from ._version import __version__
except ImportError:
    # Fallback when using the package in dev mode without installing
    # in editable mode with pip. It is highly recommended to install
    # the package from a stable release or in editable mode: https://pip.pypa.io/en/stable/topics/local-project-installs/#editable-installs
    import warnings
    warnings.warn("Importing 'jupyterlab_fold_all_code_extension' outside a proper installation.")
    __version__ = "dev"

from .preprocessor import RemoveFoldedCodePreprocessor


def _jupyter_labextension_paths():
    return [{
        "src": "labextension",
        "dest": "jupyterlab_fold_all_code_extension"
    }]


def _jupyter_server_extension_points():
    """
    Returns a list of dictionaries with metadata describing
    where to find the `_load_jupyter_server_extension` function.
    """
    return [{"module": "jupyterlab_fold_all_code_extension"}]


def _load_jupyter_server_extension(server_app):
    """
    Configure nbconvert exporters to use our preprocessor.

    This function is called when the jupyter_server extension is loaded.
    It adds the RemoveFoldedCodePreprocessor to the default preprocessor
    list for all nbconvert exporters, ensuring that folded code cells
    are hidden in exports via JupyterLab's "Export Notebook As" menu.
    """
    from nbconvert.exporters.base import Exporter

    # Get existing preprocessors (default is empty list)
    existing = list(Exporter.preprocessors.default())

    # Add our preprocessor to the default list
    preprocessor_class = 'jupyterlab_fold_all_code_extension.RemoveFoldedCodePreprocessor'
    if preprocessor_class not in existing:
        Exporter.preprocessors.default_value = existing + [preprocessor_class]

    server_app.log.info(
        "jupyterlab_fold_all_code_extension: Registered RemoveFoldedCodePreprocessor for exports"
    )
