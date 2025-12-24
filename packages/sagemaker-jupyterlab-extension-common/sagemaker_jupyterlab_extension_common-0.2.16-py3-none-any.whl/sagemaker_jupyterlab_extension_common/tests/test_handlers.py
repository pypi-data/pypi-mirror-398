import json
import platform
from sagemaker_jupyterlab_extension_common.util.app_metadata import (
    get_space_name,
    get_aws_account_id,
)
import pytest
import os
import asyncio
from datetime import datetime
from unittest.mock import ANY, Mock, patch, MagicMock
from ..handlers import register_handlers

from sagemaker_jupyterlab_extension_common.constants import (
    LOGFILE_ENV_NAME,
    JUPYTERLAB_OPERATION_LOG_FILE_NAME,
)

from .utils import (
    get_last_entry,
)


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
    register_handlers(mock_nb_app)
    mock_web_app.add_handlers.assert_called_once_with(".*$", ANY)


# @pytest.mark.asynciox
# TODO: debug the issue, succeeds in dryrun build
@pytest.mark.skipif(platform.system() == "Darwin", reason="Test skipped on macOS")
async def test_post_ui_log_events(jp_fetch):
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
                    "Message": "Error occuured in API",
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
        "/aws/sagemaker/api/eventlog", method="POST", body=json.dumps(request)
    )
    data = get_last_entry(JUPYTERLAB_OPERATION_LOG_FILE_NAME)
    assert data["Level"] == "INFO"
    assert data["Message"] == "Error occuured in API"
    assert data["Context"]["ExtensionName"] == "UIExtension"
    assert data["Context"]["ExtensionVersion"] == "1.0"


# TODO: debug the issue, succeeds in dryrun build
@pytest.mark.skipif(platform.system() == "Darwin", reason="Test skipped on macOS")
@patch(
    "sagemaker_jupyterlab_extension_common.util.file_watcher.WatchedJsonFile.get_key"
)
async def test_post_ui_log_events_with_inject(get_key_mock, jp_fetch):
    # Since this log writing handler it doesn't send any response to client
    # For this we will set the logging directroy path to write log to,
    # Read log file and clean it up.
    get_space_name.cache_clear()
    get_aws_account_id.cache_clear()
    os.environ["AWS_ACCOUNT_ID"] = "112233445566"
    get_key_mock.return_value = "test-space"

    # Create a temporary log file for logger to write
    # file_path = set_log_file_directory(LOGFILE_ENV_NAME)
    # file = os.path.join(file_path, JUPYTERLAB_OPERATION_LOG_FILE_NAME)

    publishtime = str(datetime.utcnow())

    request = {
        "events": [
            {
                "schema": "http://sagemaker.studio.jupyterlab.ui.log.schema",
                "publishTime": publishtime,
                "body": {
                    "Message": "Error occuured in API",
                    "Level": "INFO",
                    "Name": "SomeValidationError",
                    "Context": {
                        "AccountId": "__INJECT__",
                        "SpaceName": "__INJECT__",
                        "SessionId": "someSessionId",
                        "ExtensionName": "UIExtension",
                        "ExtensionVersion": "1.0",
                    },
                },
            }
        ]
    }
    response = await jp_fetch(
        "/aws/sagemaker/api/eventlog", method="POST", body=json.dumps(request)
    )
    data = get_last_entry(JUPYTERLAB_OPERATION_LOG_FILE_NAME)
    assert data["Level"] == "INFO"
    assert data["Message"] == "Error occuured in API"
    assert data["Context"]["ExtensionName"] == "UIExtension"
    assert data["Context"]["ExtensionVersion"] == "1.0"
    assert data["Context"]["SessionId"] == "someSessionId"
    assert data["Context"]["AccountId"] == "112233445566"
    assert data["Context"]["SpaceName"] == "test-space"


@patch("os.environ.get", return_value="true")
async def test_get_recovery_mode(mock_get, jp_fetch):
    response = await jp_fetch("/aws/sagemaker/api/recovery-mode", method="GET")
    response_data = json.loads(response.body.decode())
    assert response.code == 200
    assert response_data["sagemakerRecoveryMode"] == "true"
