import os
from unittest.mock import patch, mock_open

from sagemaker_jupyterlab_extension_common.util.app_metadata import (
    get_region_name,
    get_stage,
    get_domain_id,
    get_user_profile_name,
    get_aws_account_id,
    get_partition,
    get_default_aws_region,
)

TEST_USER_PROFILE = "user-jkllp12mkllll"
TEST_DOMAIN_ID = "d-jjkkyyuull"


class TestAppMetadata:
    def test_get_region_name(self):
        os.environ["AWS_REGION"] = "us-west-2"
        result = get_region_name()
        assert result == "us-west-2"
        del os.environ["AWS_REGION"]

    @patch("sagemaker_jupyterlab_extension_common.util.app_metadata.get_region_name")
    def test_get_partition(self, get_region_name_mock):
        get_region_name_mock.return_value = "us-east-2"
        result = get_partition()
        assert result == "aws"

    @patch("sagemaker_jupyterlab_extension_common.util.app_metadata.get_region_name")
    def test_get_partition_roundtable_region(self, get_region_name_mock):
        get_region_name_mock.return_value = "cn-north-1"
        result = get_partition()
        assert result == "aws-cn"

    def test_get_aws_account_id(self):
        get_aws_account_id.cache_clear()
        os.environ["AWS_ACCOUNT_ID"] = "112233445566"
        result = get_aws_account_id()
        assert result == "112233445566"

    @patch.dict(os.environ, {}, clear=True)
    @patch(
        "sagemaker_jupyterlab_extension_common.util.file_watcher.WatchedJsonFile.get_key"
    )
    def test_get_aws_account_id_from_execution_role_arn(self, get_key_mock):
        get_aws_account_id.cache_clear()
        get_key_mock.return_value = (
            "arn:aws:iam::123456789012:role/SageMakerExecutionRole"
        )
        result = get_aws_account_id()
        assert result == "123456789012"

    @patch.dict(os.environ, {}, clear=True)
    @patch(
        "sagemaker_jupyterlab_extension_common.util.file_watcher.WatchedJsonFile.get_key"
    )
    def test_get_aws_account_id_malformed_execution_role_arn(self, get_key_mock):
        get_aws_account_id.cache_clear()
        get_key_mock.return_value = "invalid-arn-format"
        result = get_aws_account_id()
        assert result == "MISSING_AWS_ACCOUNT_ID"

    @patch.dict(os.environ, {}, clear=True)
    @patch(
        "sagemaker_jupyterlab_extension_common.util.file_watcher.WatchedJsonFile.get_key"
    )
    def test_get_aws_account_id_short_execution_role_arn(self, get_key_mock):
        get_aws_account_id.cache_clear()
        get_key_mock.return_value = "arn:aws:iam"  # Only 3 parts when split by ":"
        result = get_aws_account_id()
        assert result == "MISSING_AWS_ACCOUNT_ID"

    @patch.dict(os.environ, {}, clear=True)
    @patch(
        "sagemaker_jupyterlab_extension_common.util.file_watcher.WatchedJsonFile.get_key"
    )
    def test_get_aws_account_id_none_execution_role_arn(self, get_key_mock):
        get_aws_account_id.cache_clear()
        get_key_mock.return_value = None
        result = get_aws_account_id()
        assert result == "MISSING_AWS_ACCOUNT_ID"

    @patch(
        "sagemaker_jupyterlab_extension_common.util.file_watcher.WatchedJsonFile.get_key"
    )
    def test_get_domain_id(self, get_key_mock):
        get_domain_id.cache_clear()
        get_key_mock.return_value = TEST_DOMAIN_ID
        result = get_domain_id()
        assert result == TEST_DOMAIN_ID

    @patch(
        "sagemaker_jupyterlab_extension_common.util.file_watcher.WatchedJsonFile.get_key"
    )
    def test_get_user_profile_name(self, get_key_mock):
        get_key_mock.return_value = TEST_USER_PROFILE
        result = get_user_profile_name()
        assert result == TEST_USER_PROFILE

    def test_get_default_aws_region(self):
        os.environ["AWS_DEFAULT_REGION"] = "us-west-2"
        result = get_default_aws_region()
        assert result == "us-west-2"
        del os.environ["AWS_DEFAULT_REGION"]

    @patch(
        "sagemaker_jupyterlab_extension_common.util.file_watcher.WatchedJsonFile.get_key"
    )
    def test_get_stage(self, get_key_mock):
        get_key_mock.return_value = "prod"
        get_stage.cache_clear()
        result = get_stage()
        assert result == "prod"
