from unittest.mock import patch
from sagemaker_jupyterlab_extension_common.tests.utils import get_last_entry
from sagemaker_jupyterlab_extension_common.constants import (
    JUMPSTART_SERVER_LOG_FILE_NAME,
    SERVER_LOG_FILE_NAME,
    SERVER_LOG_SCHEMA,
)
import pytest
import platform
from sagemaker_jupyterlab_extension_common.jumpstart.logging_utils import (
    JumpStartHandlerLogMixin,
)


class TestExtensionLogMixin(JumpStartHandlerLogMixin):
    jl_extension_name = "test_ext_name"
    jl_extension_version = "1.0"


# TODO: debug the issue, succeeds in dryrun build
@pytest.mark.skipif(platform.system() == "Darwin", reason="Test skipped on macOS")
@patch("sagemaker_jupyterlab_extension_common.logging.logging_utils.get_domain_id")
@patch("sagemaker_jupyterlab_extension_common.logging.logging_utils.get_aws_account_id")
@patch("sagemaker_jupyterlab_extension_common.logging.logging_utils.get_space_name")
def test_logging_mixin(
    mock_space,
    mock_aws_account,
    mock_domain,
):
    mock_space.return_value = "default-space"
    mock_domain.return_value = "d-jk12345678"
    mock_aws_account.return_value = "1234567890"

    logger = TestExtensionLogMixin()
    logger.log.error("MyTestErrorLog")

    data = get_last_entry(JUMPSTART_SERVER_LOG_FILE_NAME)
    assert data["__schema__"] == SERVER_LOG_SCHEMA
    assert data["Level"] == "ERROR"
    assert data["Message"] == "MyTestErrorLog"
    assert data["Context"]["ExtensionName"] == "test_ext_name"
    assert data["Context"]["ExtensionVersion"] == "1.0"
    assert data["Context"]["SpaceName"] == "default-space"
    assert data["Context"]["AccountId"] == "1234567890"
    assert data["Context"]["DomainId"] == "d-jk12345678"
