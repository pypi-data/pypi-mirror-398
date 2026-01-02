try:
    from ._version import __version__
except ImportError:
    # Fallback when using the package in dev mode without installing
    # in editable mode with pip. It is highly recommended to install
    # the package from a stable release or in editable mode: https://pip.pypa.io/en/stable/topics/local-project-installs/#editable-installs
    import warnings
    warnings.warn("Importing 'd5m_ai' outside a proper installation.")
    __version__ = "dev"

from .extension import D5MAIExtensionApp

def _jupyter_server_extension_points():
    return [{"module": "d5m_ai.extension", "app": D5MAIExtensionApp}]


def _jupyter_labextension_paths():
    return [{
        "src": "labextension",
        "dest": "runcell"
    }]

# Legacy support for older Jupyter versions
def _jupyter_server_extension_paths():
    return [{"module": "d5m_ai"}]

def load_jupyter_server_extension(server_app):
    """Called when the extension is loaded."""
    extension = D5MAIExtensionApp()
    server_app.web_app.add_handlers(".*$", extension.handlers)
