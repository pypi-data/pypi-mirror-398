from datetime import datetime
import json
import platform
from unittest.mock import ANY, AsyncMock, Mock, patch
import pytest
from sagemaker_jupyterlab_extension_common.jumpstart.constants import ErrorCode
from sagemaker_jupyterlab_extension_common.constants import (
    API_LOG_FILE_NAME,
    HANDLER_METRICS_SCHEMA,
    JUMPSTART_JUPYTERLAB_OPERATION_LOG_FILE_NAME,
)
from sagemaker_jupyterlab_extension_common.tests.utils import get_last_entry
from sagemaker_jupyterlab_extension_common.executor import ProcessExecutorUtility

from sagemaker_jupyterlab_extension_common.jumpstart.handlers import (
    register_jumpstart_handlers,
)
import pytest


@pytest.fixture(scope="function")
def executor():
    # Setup: Create a new ProcessPoolExecutor
    print("Initializing Executor")
    ProcessExecutorUtility.initialize_executor(max_workers=4)

    yield  # This provides the executor to the test function

    # Cleanup: Shutdown the executor once the test is done
    print("Shutting down Executor")
    ProcessExecutorUtility.shutdown_executor()


@pytest.fixture
def jp_server_config(jp_template_dir):
    return {
        "ServerApp": {
            "jpserver_extensions": {"sagemaker_jupyterlab_extension_common": True}
        },
    }


def test_mapping_added():
    mock_nb_app = Mock()
    mock_web_app = Mock()
    mock_nb_app.web_app = mock_web_app
    mock_web_app.settings = {"base_url": "nb_base_url"}
    register_jumpstart_handlers(mock_nb_app)
    mock_web_app.add_handlers.assert_called_once_with(".*$", ANY)


# TODO: debug the issue, succeeds in dryrun build
@pytest.mark.skipif(platform.system() == "Darwin", reason="Test skipped on macOS")
@patch(
    "sagemaker_jupyterlab_extension_common.jumpstart.handlers.generate_notebook_download_path"
)
@patch("sagemaker_jupyterlab_extension_common.jumpstart.handlers.save_to_ebs")
@patch("sagemaker_jupyterlab_extension_common.jumpstart.notebook_utils.get_s3_client")
async def test_post_jumpstart_notebook_handler_success(
    get_s3_client, save_to_ebs, generate_notebook_download_path, jp_fetch, executor
):
    s3_client = AsyncMock()
    get_s3_client.return_value = s3_client
    s3_client.get_object.return_value = b"mock-content"
    s3_client.head_object.return_value = {"ContentLength": 100}
    save_to_ebs.return_value = "/mock_dir/mock_file"
    generate_notebook_download_path.return_value = "mock_notebook_download_path"
    request = {
        "key": "pmm-notebooks/pmm-notebook-229.ipynb",
        "resource_type": "notebook",
        "model_id": "test-model-id",
        "endpoint_name": "test-endpoint-name",
        "inference_component": "test-inference-component",
        "hub_name": "test-hub-name",
    }
    response = await jp_fetch(
        "/aws/sagemaker/api/jumpstart/notebook", method="POST", body=json.dumps(request)
    )
    assert response.code == 200
    resp = json.loads(response.body.decode("utf-8"))
    assert resp["notebookPath"] == "/mock_dir/mock_file"


# TODO: debug the issue, succeeds in dryrun build
@pytest.mark.skipif(platform.system() == "Darwin", reason="Test skipped on macOS")
@patch(
    "sagemaker_jupyterlab_extension_common.jumpstart.handlers.generate_notebook_download_path"
)
@patch("sagemaker_jupyterlab_extension_common.jumpstart.handlers.save_to_ebs")
@patch("sagemaker_jupyterlab_extension_common.jumpstart.notebook_utils.get_s3_client")
@patch(
    "sagemaker_jupyterlab_extension_common.jumpstart.notebook_utils._get_object_size"
)
async def test_post_jumpstart_notebook_handler_500(
    _get_object_size,
    get_s3_client,
    save_to_ebs,
    generate_notebook_download_path,
    jp_fetch,
    executor,
):
    s3_client = AsyncMock()
    get_s3_client.return_value = s3_client
    s3_client.get_object.return_value = b"mock-content"
    _get_object_size.return_value = 123
    save_to_ebs.side_effect = Exception("error save to ebs")
    generate_notebook_download_path.return_value = "mock_notebook_download_path"
    request = {
        "key": "pmm-notebooks/pmm-notebook-229.ipynb",
        "resource_type": "notebook",
        "model_id": "test-model-id",
        "endpoint_name": "test-endpoint-name",
        "inference_component": "test-inference-component",
    }
    with pytest.raises(Exception) as e:
        response = await jp_fetch(
            "/aws/sagemaker/api/jumpstart/notebook",
            method="POST",
            body=json.dumps(request),
        )
    assert str(e.value) == "HTTP 500: Internal Server Error"
    data = get_last_entry(API_LOG_FILE_NAME)
    assert data["__schema__"] == HANDLER_METRICS_SCHEMA
    assert (
        data["Operation"]
        == "POST./savitur/default/aws/sagemaker/api/jumpstart/notebook"
    )
    assert data["Fault"] == 1
    assert data["Error"] == 0


# TODO: debug the issue, succeeds in dryrun build
@pytest.mark.skipif(platform.system() == "Darwin", reason="Test skipped on macOS")
@patch(
    "sagemaker_jupyterlab_extension_common.jumpstart.handlers.generate_notebook_download_path"
)
@patch("sagemaker_jupyterlab_extension_common.jumpstart.handlers.save_to_ebs")
@patch("sagemaker_jupyterlab_extension_common.jumpstart.notebook_utils.get_s3_client")
async def test_post_jumpstart_notebook_handler_400(
    get_s3_client, save_to_ebs, generate_notebook_download_path, jp_fetch, executor
):
    s3_client = AsyncMock()
    get_s3_client.return_value = s3_client
    s3_client.get_object.return_value = b"mock-content"
    save_to_ebs.side_effect = Exception("error save to ebs")
    generate_notebook_download_path.return_value = "mock_notebook_download_path"
    request = {
        "key": "pmm-notebooks/pmm-notebook-229.ipynb",
        "resource_type": "invalid_notebook",
        "model_id": "test_model_id",
        "endpoint_name": "test_endpoint_name",
        "inference_component": "test_inference_component",
    }
    with pytest.raises(Exception) as e:
        response = await jp_fetch(
            "/aws/sagemaker/api/jumpstart/notebook",
            method="POST",
            body=json.dumps(request),
        )
        assert response.json().errorCode == ErrorCode.INVALID_REQUEST
    assert str(e.value) == "HTTP 400: Bad Request"
    data = get_last_entry(API_LOG_FILE_NAME)
    assert data["__schema__"] == HANDLER_METRICS_SCHEMA
    assert (
        data["Operation"]
        == "POST./savitur/default/aws/sagemaker/api/jumpstart/notebook"
    )
    assert data["Error"] == 1
    assert data["Fault"] == 0


# TODO: debug the issue, succeeds in dryrun build
@pytest.mark.skipif(platform.system() == "Darwin", reason="Test skipped on macOS")
@patch(
    "sagemaker_jupyterlab_extension_common.jumpstart.handlers.generate_notebook_download_path"
)
@patch(
    "sagemaker_jupyterlab_extension_common.jumpstart.handlers.is_jumpstart_supported_region"
)
@patch("sagemaker_jupyterlab_extension_common.jumpstart.handlers.save_to_ebs")
@patch("sagemaker_jupyterlab_extension_common.jumpstart.notebook_utils.get_s3_client")
async def test_post_jumpstart_notebook_handler_404(
    get_s3_client,
    save_to_ebs,
    is_jumpstart_supported_region,
    generate_notebook_download_path,
    jp_fetch,
    executor,
):
    s3_client = AsyncMock()
    get_s3_client.return_value = s3_client
    s3_client.get_object.return_value = b"mock-content"
    save_to_ebs.side_effect = Exception("error save to ebs")
    is_jumpstart_supported_region.return_value = False
    generate_notebook_download_path.return_value = "mock_notebook_download_path"
    request = {
        "key": "pmm-notebooks/pmm-notebook-229.ipynb",
        "resource_type": "invalid_notebook",
        "model_id": "test_model_id",
        "endpoint_name": "test_endpoint_name",
        "inference_component": "test_inference_component",
    }
    with pytest.raises(Exception) as e:
        response = await jp_fetch(
            "/aws/sagemaker/api/jumpstart/notebook",
            method="POST",
            body=json.dumps(request),
        )
        assert response.json().errorCode == ErrorCode.NOTEBOOK_NOT_AVAILABLE
    assert str(e.value) == "HTTP 404: Not Found"
    data = get_last_entry(API_LOG_FILE_NAME)
    assert data["__schema__"] == HANDLER_METRICS_SCHEMA
    assert (
        data["Operation"]
        == "POST./savitur/default/aws/sagemaker/api/jumpstart/notebook"
    )
    assert data["Error"] == 1
    assert data["Fault"] == 0


# TODO: debug the issue, succeeds in dryrun build
@pytest.mark.skipif(platform.system() == "Darwin", reason="Test skipped on macOS")
async def test_post_ui_log_events_handler_success(jp_fetch):
    # Since this log writing handler it doesn't send any response to client
    # For this we will set the logging directroy path to write log to,
    # Read log file and clean it up.

    publishtime = str(datetime.utcnow())

    request = {
        "events": [
            {
                "schema": "http://sagemaker.studio.jupyterlab.ui.log.schema",
                "publishTime": publishtime,
                "body": {
                    "Message": "Error occurred in API",
                    "Level": "INFO",
                    "Name": "SomeValidationError",
                    "Context": {
                        "SessionId": "someSessionId",
                        "ExtensionName": "UIExtension",
                        "ExtensionVersion": "1.0",
                    },
                },
            }
        ]
    }
    response = await jp_fetch(
        "/aws/sagemaker/api/jumpstart/eventlog", method="POST", body=json.dumps(request)
    )
    data = get_last_entry(JUMPSTART_JUPYTERLAB_OPERATION_LOG_FILE_NAME)
    assert data["Level"] == "INFO"
    assert data["Message"] == "Error occurred in API"
    assert data["Context"]["ExtensionName"] == "UIExtension"
    assert data["Context"]["ExtensionVersion"] == "1.0"
