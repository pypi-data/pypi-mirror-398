import json
import logging
import os
import os.path
from enum import Enum
from pathlib import Path

from traitlets import log
from jupyter_events.logger import EventLogger
from jupyter_events.schema_registry import SchemaRegistryException
from aws_embedded_metrics.logger.metrics_context import MetricsContext
from aws_embedded_metrics.serializers.log_serializer import LogSerializer

from sagemaker_jupyterlab_extension_common.util.app_metadata import (
    get_domain_id,
    get_aws_account_id,
    get_space_name,
)


from sagemaker_jupyterlab_extension_common.constants import (
    JUMPSTART_JUPYTERLAB_OPERATION_LOG_FILE_NAME,
    JUMPSTART_SERVER_LOG_FILE_NAME,
    SERVER_LOG_SCHEMA,
    HANDLER_METRICS_SCHEMA,
    LOGFILE_ENV_NAME,
    SERVER_LOG_FILE_NAME,
    API_LOG_FILE_NAME,
    REQUEST_LOG_FILE_NAME,
    SCHEMAS_DIR,
    JUPYTERLAB_OPERATION_LOG_FILE_NAME,
    JUPYTERLAB_METRICS_LOG_FILE_NAME,
)


class SchemaDocument(Enum):
    Operational = ("log_schema.yml", SERVER_LOG_FILE_NAME)
    HandlerMetrics = (
        "handler_metrics_schema.yml",
        API_LOG_FILE_NAME,
    )
    RequestMetrics = (
        "request_metrics_schema.yml",
        REQUEST_LOG_FILE_NAME,
    )
    JupyterLabOperation = (
        "jupyterlab_operation_log_schema.yml",
        JUPYTERLAB_OPERATION_LOG_FILE_NAME,
    )
    JupyterLabPerformanceMetrics = (
        "jupyterlab_client_performance_metrics_schema.yml",
        JUPYTERLAB_METRICS_LOG_FILE_NAME,
    )
    JumpStartOperational = ("log_schema.yml", JUMPSTART_SERVER_LOG_FILE_NAME)
    JumpStartJupyterLabOperation = (
        "jupyterlab_operation_log_schema.yml",
        JUMPSTART_JUPYTERLAB_OPERATION_LOG_FILE_NAME,
    )

    def __init__(self, schema_file_name, log_file_name):
        here = os.path.abspath(os.path.dirname(__file__))
        self.schema_file_path = (
            None
            if schema_file_name is None
            else Path(__file__).parent.joinpath(here, SCHEMAS_DIR, schema_file_name)
        )
        self.log_file_name = log_file_name

    def get_schema_file_path(self):
        if self.schema_file_path is None:
            return None
        return self.schema_file_path

    def get_log_file_name(self):
        return self.log_file_name

    def get_log_event_schemas(self):
        return list(
            filter(lambda schema: schema.schema_document == self, LogEventSchema)
        )

    def get_log_event_filter(self):
        return SchemaDocumentLogFilter(self)


def get_handler(schema_document):
    log_file_env_path = os.environ.get(LOGFILE_ENV_NAME, "/var/log/studio/")

    # Append the jupyterlab folder at the end of the path read from env.
    # the / at the end of jupyterlab signifies that its the directory and not file
    logging_dir_name = os.path.join(os.path.dirname(log_file_env_path), "jupyterlab/")
    try:
        log_file_path = os.path.join(
            logging_dir_name, schema_document.get_log_file_name()
        )
        os.makedirs(logging_dir_name, exist_ok=True)
        handler = logging.FileHandler(log_file_path)
    except Exception as e:
        print("Log file ", log_file_path, " is not writable, using stdout")
        handler = logging.StreamHandler()
    return handler


def get_eventlog():
    """
    Construct the jupyter EventLog object for this logger
    """
    return EventLogger()


_default_eventlog = get_eventlog()


class OperationalLoggingHandler(logging.Handler):
    """A logging handler that uses an eventlog"""

    def __init__(self, extension_name, extension_version):
        logging.Handler.__init__(self)
        self.extension_name = extension_name
        self.extension_version = extension_version

    def emit(self, record):
        event = _get_event_capsule()
        event["Context"]["ExtensionName"] = self.extension_name
        event["Context"]["ExtensionVersion"] = self.extension_version
        if record.__dict__.get("Component") is not None:
            event["Context"]["Component"] = record.__dict__.get("Component")
        if (
            hasattr(record, "client_request_id")
            and record.client_request_id is not None
        ):
            event["Context"]["ClientRequestId"] = record.client_request_id
        if (
            hasattr(record, "server_request_id")
            and record.server_request_id is not None
        ):
            event["Context"]["ServerRequestId"] = record.server_request_id
        exc_info = record.__dict__.get("exc_info")
        if exc_info and len(exc_info) >= 2:
            event["Name"] = str(exc_info[0])
        event.update(
            dict(
                Level=record.levelname,
                Message=record.getMessage(),
            )
        )
        eventlog = self.eventlog
        eventlog.emit(schema_id=SERVER_LOG_SCHEMA, data=event)


def _get_event_capsule():
    return dict(
        Context=dict(
            DomainId=get_domain_id(),
            AccountId=get_aws_account_id(),
            SpaceName=get_space_name(),
        )
    )


def get_operational_logger(
    obj,
    eventlog=None,
    extension_name=None,
    extension_version=None,
    schema=SchemaDocument.Operational,
):
    """Creates a custom logger for an object.

    It will extend the standard Jupyter logger.
    """
    parent_log = log.get_logger()
    child_log = parent_log.getChild(obj.__class__.__name__)

    # If handler already exists skip adding it
    # Otherwise we see same lines printed multiple times
    for handler in child_log.handlers:
        if isinstance(handler, OperationalLoggingHandler):
            return child_log

    if eventlog is None:
        eventlog = _default_eventlog

    # Add a handler for the log file.
    _log_handler = OperationalLoggingHandler(extension_name, extension_version)
    _log_handler.setLevel(logging.DEBUG)
    _log_handler.eventlog = eventlog

    # configure event logger for operational logging
    handler = get_handler(schema)
    _log_handler.eventlog.register_handler(handler)
    try:
        _log_handler.eventlog.register_event_schema(schema.get_schema_file_path())
    except Exception as ex:
        logging.warning(f"Schema is already registered {ex}")

    child_log.addHandler(_log_handler)
    return child_log


class MetricWriter:
    def __init__(self, ext_name, ext_version):
        self.extension_name = ext_name
        self.extension_version = ext_version
        self.metric_namsepace = "JupyterServer"
        self.eventlog = _create_metric_logger()

    def put_error(self, operation, **kwargs):
        json_metrics = self._create_metric_context(**kwargs)
        metric_name = kwargs.get("MetricName")
        self._emit_metric_log(metric_name, json_metrics, operation, fault=0, error=1)

    def put_fault(self, operation, **kwargs):
        metric_name = kwargs.get("MetricName")
        json_metrics = self._create_metric_context(**kwargs)
        self._emit_metric_log(metric_name, json_metrics, operation, fault=1, error=0)

    def record_latency(self, operation, **kwargs):
        metric_name = kwargs.get("MetricName")
        json_metrics = self._create_metric_context(**kwargs)
        latency = kwargs.get("MetricValue")
        self._emit_metric_log(
            metric_name, json_metrics, operation, fault=0, error=0, latencyms=latency
        )

    def _create_metric_context(self, **kwargs):
        metric_name = kwargs.get("MetricName")
        metric_value = kwargs.get("MetricValue")
        metric_unit = kwargs.get("MetricUnit")
        dimensions = kwargs.get("Dimensions")
        # namespace is already setup as part of server extension
        metrics_ctx = MetricsContext().empty()
        metrics_ctx.namespace = self.metric_namsepace
        for dim in dimensions:
            metrics_ctx.put_dimensions(dim)
        metrics_ctx.put_metric(metric_name, metric_value, metric_unit)
        json_metrics = json.loads(LogSerializer.serialize(metrics_ctx)[0])
        return json_metrics

    def _emit_metric_log(
        self, metric_name, json_metrics, operation, fault=0, error=0, latencyms=0
    ):
        try:
            event = _get_event_capsule()
            event["Context"]["ExtensionName"] = self.extension_name
            event["Context"]["ExtensionVersion"] = self.extension_version
            event.update(dict(Operation=operation, Fault=fault, Error=error))
            if metric_name == "LatencyMS":
                event["LatencyMS"] = latencyms
            event.update(json_metrics)
            self.eventlog.emit(schema_id=HANDLER_METRICS_SCHEMA, data=event)
        except:
            logging.warning(
                f"Unable to log metric for metric_name: {metric_name}",
                exc_info=1,
            )
            return {}


def _create_metric_logger():
    eventlog = get_eventlog()
    handler = get_handler(SchemaDocument.HandlerMetrics)
    eventlog.register_handler(handler)
    eventlog.register_event_schema(SchemaDocument.HandlerMetrics.get_schema_file_path())
    return eventlog


def get_api_metric_logger(self, ext_name, ext_ver):
    if isinstance(self, MetricWriter):
        return self
    return MetricWriter(ext_name, ext_ver)


class HandlerLogMixin:
    """Add a custom logger to a handler.

    This class must come before the Handler class in mro order, e.g.

    class Foo(HandlerLogMixin, IPythonHandler):
      pass
    """

    eventlog = None
    jl_extension_name = None
    jl_extension_version = None

    @property
    def log(self):
        return get_operational_logger(
            self, self.eventlog, self.jl_extension_name, self.jl_extension_version
        )

    @property
    def metric(self):
        return get_api_metric_logger(
            self, self.jl_extension_name, self.jl_extension_version
        )


def create_ui_eventlogger(schema_documents):
    eventlog = _default_eventlog
    for schema_document in schema_documents:
        try:
            handler = get_handler(schema_document)
            # Add filter for handler
            handler.addFilter(schema_document.get_log_event_filter())
            eventlog.register_handler(handler)
            eventlog.register_event_schema(schema_document.get_schema_file_path())
        except SchemaRegistryException:
            pass
    return eventlog


class SchemaDocumentLogFilter:
    def __init__(self, schema_document):
        self.schema_document = schema_document
        self.schema_filter = list(
            map(
                lambda schema: schema.schema_id, schema_document.get_log_event_schemas()
            )
        )

    def filter(self, record):
        if (
            not record
            or not record.msg
            or not record.msg["__schema__"]
            or not "__schema__" in record.msg
        ):
            return False
        return record.msg["__schema__"] in self.schema_filter


schema_dict = {}


class LogEventSchema(Enum):
    JupyterLabOperationalLogEvent = (
        "http://sagemaker.studio.jupyterlab.ui.log.schema",
        SchemaDocument.JupyterLabOperation,
    )
    JupyterLabPerformanceMetricsEvent = (
        "http://sagemaker.studio.jupyterlab.ui.performance.schema",
        SchemaDocument.JupyterLabPerformanceMetrics,
    )
    JumpStartJupyterLabOperationalLogEvent = (
        "http://sagemaker.studio.jupyterlab.ui.log.schema",
        SchemaDocument.JumpStartJupyterLabOperation,
    )

    def __init__(self, schema_id, schema_document):
        self.schema_id = schema_id
        self.schema_document = schema_document
        schema_dict[schema_id] = self

    @staticmethod
    def from_schema_name(schema_id):
        return schema_dict[schema_id] if schema_id in schema_dict else None
