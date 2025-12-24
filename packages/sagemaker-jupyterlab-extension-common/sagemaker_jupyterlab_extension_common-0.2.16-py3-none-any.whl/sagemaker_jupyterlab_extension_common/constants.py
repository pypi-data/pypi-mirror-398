# Common Constants
from .dual_stack_utils import is_dual_stack_enabled

LOGFILE_ENV_NAME = "SAGEMAKER_LOG_FILE"
SCHEMAS_DIR = "schemas/"

# Jupyter Server constants for Log files and schema
SERVER_LOG_FILE_NAME = "sm-jupyter-server-ext.log"
API_LOG_FILE_NAME = "sm-jupyter-server-ext.api.log"
REQUEST_LOG_FILE_NAME = "sm-jupyter-server-ext.requests.log"
SERVER_LOG_SCHEMA = "http://sagemaker.studio.jupyterserver.log.schema"
HANDLER_METRICS_SCHEMA = "http://sagemaker.studio.jupyterserver.api.metric.schema"
REQUEST_METRICS_SCHEMA = (
    "http://sagemaker.studio.jupyterserver.httprequest.metric.schema"
)

# JupyterLab constants for Log files and schema
JUPYTERLAB_OPERATION_LOG_FILE_NAME = "sm-jupyterlab-ext.ui.log"
JUPYTERLAB_METRICS_LOG_FILE_NAME = "sm-jupyterlab-ext.ui.metrics.log"
JUPYTERLAB_OPERATIONAL_LOG_SCHEMA = "http://sagemaker.studio.jupyterlab.ui.log.schema"
JUPYTERLAB_PERFORMANCE_METRICS_LOG_SCHEMA = (
    "http://sagemaker.studio.jupyterlab.ui.performance.schema"
)

# JumpStart Jupyter Server constants for Log files and schema
JUMPSTART_SERVER_LOG_FILE_NAME = "sm-jumpstart-jupyter-server-ext.log"
JUMPSTART_JUPYTERLAB_OPERATION_LOG_FILE_NAME = "sm-jumpstart-jupyterlab-ext.ui.log"

CONTEXT_INJECT_PLACEHOLDER = "__INJECT__"
DEFAULT_HOME_DIRECTORY = "/home/sagemaker-user"

USE_DUALSTACK_ENDPOINT = is_dual_stack_enabled()
