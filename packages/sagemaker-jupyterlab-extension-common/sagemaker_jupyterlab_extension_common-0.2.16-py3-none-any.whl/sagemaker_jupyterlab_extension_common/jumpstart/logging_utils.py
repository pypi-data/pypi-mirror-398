import datetime
import logging

from sagemaker_jupyterlab_extension_common.jumpstart.request import (
    client_request_id_var,
    server_request_id_var,
)
from sagemaker_jupyterlab_extension_common.util.metric_util import (
    MetricUnit,
    create_metric_context,
)
from sagemaker_jupyterlab_extension_common.logging.logging_utils import (
    HandlerLogMixin,
    SchemaDocument,
    get_eventlog,
    get_operational_logger,
)
from .._version import __version__ as ext_version

_default_event_log = get_eventlog()
EXTENSION_NAME = "sagemaker_jupyterlab_extension_common"
EXTENSION_VERSION = ext_version
OPERATION = f"POST./savitur/default/aws/sagemaker/api/jumpstart/notebook"
API_NAME = "GetJumpStartNotebook"


class JumpStartHandlerLogMixin(HandlerLogMixin):
    """Add a JumpStart custom logger to a handler.

    This log handler write to a jumpstart-owned  file location `sm-js-jupyter-server-ext.log`
    This class must come before the Handler class in mro order, e.g.

    class Foo(JumpStartHandlerLogMixin, IPythonHandler):
      pass
    """

    eventlog = _default_event_log
    jl_extension_name = EXTENSION_NAME
    jl_extension_version = EXTENSION_VERSION

    @property
    def log(self):
        logger = get_operational_logger(
            self,
            self.eventlog,
            self.jl_extension_name,
            self.jl_extension_version,
            SchemaDocument.JumpStartOperational,
        )
        request_id_filter = RequestIdLogFilter()
        logger.addFilter(request_id_filter)
        return logger

    def _emit_error_metric(self) -> None:
        error_context = create_metric_context(
            "Error",
            API_NAME,
            OPERATION,
            1,
            MetricUnit.Count,
        )
        self.metric.put_error(OPERATION, **error_context)

    def _emit_fault_metric(self) -> None:
        fault_context = create_metric_context(
            "Fault",
            API_NAME,
            OPERATION,
            1,
            MetricUnit.Count,
        )
        self.metric.put_fault(OPERATION, **fault_context)

    def _emit_latency_metric(self, elapsedTime: datetime.datetime) -> None:
        latency_context = create_metric_context(
            "LatencyMS",
            API_NAME,
            OPERATION,
            int(elapsedTime.total_seconds() * 1000),
            MetricUnit.Milliseconds,
        )
        self.metric.record_latency(OPERATION, **latency_context)


class RequestIdLogFilter(logging.Filter):
    def filter(self, record) -> bool:
        record.client_request_id = client_request_id_var.get()
        record.server_request_id = server_request_id_var.get()
        return True
