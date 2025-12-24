import json
from os import path
from pathlib import Path
from .handlers import register_handlers
from .jumpstart.handlers import register_jumpstart_handlers

from ._version import __version__

HERE = Path(__file__).parent.resolve()
with (HERE / "labextension" / "package.json").open(encoding="utf-8") as fid:
    data = json.load(fid)


# Path to the frontend JupyterLab extension assets
def _jupyter_labextension_paths():
    return [{"src": "labextension", "dest": data["name"]}]


def _jupyter_server_extension_points():
    return [{"module": "sagemaker_jupyterlab_extension_common"}]


# Entrypoint of the server extension
def _load_jupyter_server_extension(nb_app):
    nb_app.log.info(
        f"Loading SageMaker JupyterLab common server extension {__version__}"
    )
    register_handlers(nb_app)
    register_jumpstart_handlers(nb_app)


load_jupyter_server_extension = _load_jupyter_server_extension
