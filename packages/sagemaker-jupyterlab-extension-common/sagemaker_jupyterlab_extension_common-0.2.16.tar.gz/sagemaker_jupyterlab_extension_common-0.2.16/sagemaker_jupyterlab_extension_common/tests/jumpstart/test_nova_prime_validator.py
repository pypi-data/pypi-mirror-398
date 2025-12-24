import unittest
from unittest.mock import MagicMock, patch, call
import logging
import botocore.exceptions

from sagemaker_jupyterlab_extension_common.jumpstart.nova_prime_validator import (
    _check_s3_prime_access,
    _check_direct_prime_status,
    check_prime_status,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger(__name__)


class test_nova_prime_validator(unittest.TestCase):

    def setUp(self):
        self.mock_s3_client = MagicMock()
        self.mock_sts_client = MagicMock()
        self.mock_datazone_client = MagicMock()
        self.mock_boto3_session = MagicMock()

        # Patch boto3.client and boto3.Session
        self.patcher_boto3_client = patch("boto3.client", autospec=True)
        self.mock_boto3_client = self.patcher_boto3_client.start()
        self.mock_boto3_client.side_effect = self._mock_boto3_client_side_effect

        self.patcher_boto3_session = patch("boto3.Session", autospec=True)
        self.mock_boto3_session_constructor = self.patcher_boto3_session.start()
        self.mock_boto3_session_constructor.return_value = self.mock_boto3_session

        # Mock session returns the mock client
        self.mock_boto3_session.client.side_effect = (
            self._mock_boto3_session_client_side_effect
        )

        # Capture actual logging output during tests
        self.log_capture_handler = logging.Handler()
        logging.getLogger().addHandler(self.log_capture_handler)
        self.log_capture_handler.setFormatter(
            logging.Formatter("%(levelname)s:%(name)s:%(message)s")
        )
        self.log_capture_handler.records = []  # To store log records
        self.log_capture_handler.emit = (
            lambda record: self.log_capture_handler.records.append(record)
        )

    def tearDown(self):
        self.patcher_boto3_client.stop()
        self.patcher_boto3_session.stop()
        logging.getLogger().removeHandler(self.log_capture_handler)

    def _mock_boto3_client_side_effect(self, service_name, region_name=None):
        """Side effect for boto3.client to return specific mock clients."""
        if service_name == "s3":
            return self.mock_s3_client
        elif service_name == "sts":
            return self.mock_sts_client
        elif service_name == "datazone":
            return self.mock_datazone_client
        raise ValueError(f"Unexpected service client requested: {service_name}")

    def _mock_boto3_session_client_side_effect(self, service_name, region_name=None):
        """Side effect for boto3.Session().client to return specific mock clients."""
        return self._mock_boto3_client_side_effect(service_name, region_name)

    # Test Case 1: Ensures _check_s3_prime_access returns False with AccessDenied, simulating a non-allowlisted account.
    def test_check_s3_prime_access_for_non_allowlisted_account(self):
        self.mock_s3_client.get_object.side_effect = botocore.exceptions.ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access Denied"}}, "GetObject"
        )
        result = _check_s3_prime_access(
            session=self.mock_boto3_session,
            model_id="any-model",
            region="us-east-1",
            account_id="999999999999",  # Account ID that should not have access
            caller_arn="arn:aws:iam::999999999999:role/SomeRole",
        )
        self.assertFalse(result)
        self.mock_s3_client.get_object.assert_called_once()
        self.assertIn(
            "Prime access check FAILED", self.log_capture_handler.records[-2].message
        )
        self.assertIn(
            "ACTION REQUIRED: The role used (or the policy on the Access Point) does not have 's3:GetObject' permissions",
            self.log_capture_handler.records[-1].message,
        )

    # Test Case 2: Project role and connection role both have prime access (resolves to prime access verified)
    @patch(
        "sagemaker_jupyterlab_extension_common.jumpstart.nova_prime_validator._get_datazone_connection_details",
        return_value={
            "physicalEndpoints": [
                {"awsLocation": {"awsAccountId": "123", "awsRegion": "us-east-1"}}
            ],
            "connectionCredentials": {
                "accessKeyId": "abc",
                "secretAccessKey": "def",
                "sessionToken": "ghi",
            },
            "environmentUserRole": "arn:aws:iam::123:role/ProjectRole",
        },
    )
    @patch(
        "sagemaker_jupyterlab_extension_common.jumpstart.nova_prime_validator._check_connection_role_prime_access",
        return_value=True,
    )
    @patch(
        "sagemaker_jupyterlab_extension_common.jumpstart.nova_prime_validator._check_project_role_prime_access",
        return_value=True,
    )
    def test_check_prime_status_datazone_both_access_verified(
        self, mock_project_role_access, mock_connection_role_access, mock_get_details
    ):
        result = check_prime_status("model", "us-east-1", "domain_id", "conn_id")
        self.assertTrue(result)
        mock_get_details.assert_called_once()
        mock_connection_role_access.assert_called_once()
        mock_project_role_access.assert_called_once()
        self.assertIn(
            "Both DataZone Connection Role AND Project Role have prime access",
            self.log_capture_handler.records[-1].message,
        )

    # Test Case 3: Project role and connection role both don't have prime access (resolves to no prime access)
    @patch(
        "sagemaker_jupyterlab_extension_common.jumpstart.nova_prime_validator._get_datazone_connection_details",
        return_value={
            "physicalEndpoints": [
                {"awsLocation": {"awsAccountId": "123", "awsRegion": "us-east-1"}}
            ],
            "connectionCredentials": {
                "accessKeyId": "abc",
                "secretAccessKey": "def",
                "sessionToken": "ghi",
            },
            "environmentUserRole": "arn:aws:iam::123:role/ProjectRole",
        },
    )
    @patch(
        "sagemaker_jupyterlab_extension_common.jumpstart.nova_prime_validator._check_connection_role_prime_access",
        return_value=False,
    )
    @patch(
        "sagemaker_jupyterlab_extension_common.jumpstart.nova_prime_validator._check_project_role_prime_access",
        return_value=False,
    )
    def test_check_prime_status_datazone_both_no_access(
        self, mock_project_role_access, mock_connection_role_access, mock_get_details
    ):
        result = check_prime_status("model", "us-east-1", "domain_id", "conn_id")
        self.assertFalse(result)
        self.assertIn(
            "One or both roles lack prime access",
            self.log_capture_handler.records[-1].message,
        )

    # Test Case 4: Project role has prime access, connection role does not (resolves to no prime access)
    @patch(
        "sagemaker_jupyterlab_extension_common.jumpstart.nova_prime_validator._get_datazone_connection_details",
        return_value={
            "physicalEndpoints": [
                {"awsLocation": {"awsAccountId": "123", "awsRegion": "us-east-1"}}
            ],
            "connectionCredentials": {
                "accessKeyId": "abc",
                "secretAccessKey": "def",
                "sessionToken": "ghi",
            },
            "environmentUserRole": "arn:aws:iam::123:role/ProjectRole",
        },
    )
    @patch(
        "sagemaker_jupyterlab_extension_common.jumpstart.nova_prime_validator._check_connection_role_prime_access",
        return_value=False,
    )
    @patch(
        "sagemaker_jupyterlab_extension_common.jumpstart.nova_prime_validator._check_project_role_prime_access",
        return_value=True,
    )
    def test_check_prime_status_datazone_conn_role_fails(
        self, mock_project_role_access, mock_connection_role_access, mock_get_details
    ):
        result = check_prime_status("model", "us-east-1", "domain_id", "conn_id")
        self.assertFalse(result)
        self.assertIn(
            "One or both roles lack prime access",
            self.log_capture_handler.records[-1].message,
        )

    # Test Case 5: Connection role has prime access, project role does not (resolves to no prime access)
    @patch(
        "sagemaker_jupyterlab_extension_common.jumpstart.nova_prime_validator._get_datazone_connection_details",
        return_value={
            "physicalEndpoints": [
                {"awsLocation": {"awsAccountId": "123", "awsRegion": "us-east-1"}}
            ],
            "connectionCredentials": {
                "accessKeyId": "abc",
                "secretAccessKey": "def",
                "sessionToken": "ghi",
            },
            "environmentUserRole": "arn:aws:iam::123:role/ProjectRole",
        },
    )
    @patch(
        "sagemaker_jupyterlab_extension_common.jumpstart.nova_prime_validator._check_connection_role_prime_access",
        return_value=True,
    )
    @patch(
        "sagemaker_jupyterlab_extension_common.jumpstart.nova_prime_validator._check_project_role_prime_access",
        return_value=False,
    )
    def test_check_prime_status_datazone_proj_role_fails(
        self, mock_project_role_access, mock_connection_role_access, mock_get_details
    ):
        result = check_prime_status("model", "us-east-1", "domain_id", "conn_id")
        self.assertFalse(result)
        self.assertIn(
            "One or both roles lack prime access",
            self.log_capture_handler.records[-1].message,
        )

    # Test Case 6: Direct prime access to an account that has prime access
    @patch(
        "sagemaker_jupyterlab_extension_common.jumpstart.nova_prime_validator._check_direct_prime_status",
        return_value=True,
    )
    def test_check_prime_status_direct_access_success(self, mock_direct_status):
        result = check_prime_status("model", "us-east-1")
        self.assertTrue(result)
        mock_direct_status.assert_called_once()

    # Test Case 7: No direct prime access to an account that has no prime access
    @patch(
        "sagemaker_jupyterlab_extension_common.jumpstart.nova_prime_validator._check_direct_prime_status",
        return_value=False,
    )
    def test_check_prime_status_direct_access_fails(self, mock_direct_status):
        result = check_prime_status("model", "us-east-1")
        self.assertFalse(result)
        mock_direct_status.assert_called_once()

    # --- Tests for _check_s3_prime_access ---
    def test_check_s3_prime_access_success(self):
        self.mock_s3_client.get_object.return_value = {}
        result = _check_s3_prime_access(
            session=self.mock_boto3_session,
            model_id="test-model",
            region="us-east-1",
            account_id="123456789012",
            caller_arn="arn:aws:iam::123456789012:role/TestRole",
        )
        self.assertTrue(result)
        self.mock_s3_client.get_object.assert_called_once()
        self.assertIn(
            "Prime access VERIFIED", self.log_capture_handler.records[-1].message
        )

    def test_check_s3_prime_access_denied(self):
        self.mock_s3_client.get_object.side_effect = botocore.exceptions.ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access Denied"}}, "GetObject"
        )
        result = _check_s3_prime_access(
            session=self.mock_boto3_session,
            model_id="test-model",
            region="us-east-1",
            account_id="123456789012",
            caller_arn="arn:aws:iam::123456789012:role/TestRole",
        )
        self.assertFalse(result)
        self.assertIn(
            "Prime access check FAILED", self.log_capture_handler.records[-2].message
        )
        self.assertIn(
            "ACTION REQUIRED: The role used",
            self.log_capture_handler.records[-1].message,
        )

    def test_check_s3_prime_access_no_such_key(self):
        self.mock_s3_client.get_object.side_effect = botocore.exceptions.ClientError(
            {"Error": {"Code": "NoSuchKey", "Message": "Key does not exist"}},
            "GetObject",
        )
        result = _check_s3_prime_access(
            session=self.mock_boto3_session,
            model_id="test-model",
            region="us-east-1",
            account_id="123456789012",
            caller_arn="arn:aws:iam::123456789012:role/TestRole",
        )
        self.assertFalse(result)
        self.assertIn(
            "Prime access check FAILED", self.log_capture_handler.records[-2].message
        )
        self.assertIn(
            "ACTION REQUIRED: The object", self.log_capture_handler.records[-1].message
        )

    def test_check_s3_prime_access_no_such_bucket(self):
        self.mock_s3_client.get_object.side_effect = botocore.exceptions.ClientError(
            {"Error": {"Code": "NoSuchBucket", "Message": "Bucket does not exist"}},
            "GetObject",
        )
        result = _check_s3_prime_access(
            session=self.mock_boto3_session,
            model_id="test-model",
            region="us-east-1",
            account_id="123456789012",
            caller_arn="arn:aws:iam::123456789012:role/TestRole",
        )
        self.assertFalse(result)
        self.assertIn(
            "Prime access check FAILED", self.log_capture_handler.records[-2].message
        )
        self.assertIn(
            "ACTION REQUIRED: The S3 Access Point",
            self.log_capture_handler.records[-1].message,
        )

    def test_check_s3_prime_access_generic_client_error(self):
        self.mock_s3_client.get_object.side_effect = botocore.exceptions.ClientError(
            {"Error": {"Code": "SomeOtherError", "Message": "Generic client error"}},
            "GetObject",
        )
        result = _check_s3_prime_access(
            session=self.mock_boto3_session,
            model_id="test-model",
            region="us-east-1",
            account_id="123456789012",
            caller_arn="arn:aws:iam::123456789012:role/TestRole",
        )
        self.assertFalse(result)
        self.assertIn(
            "Prime access check FAILED", self.log_capture_handler.records[-1].message
        )

    def test_check_s3_prime_access_unexpected_exception(self):
        self.mock_s3_client.get_object.side_effect = Exception("Network issue")
        result = _check_s3_prime_access(
            session=self.mock_boto3_session,
            model_id="test-model",
            region="us-east-1",
            account_id="123456789012",
            caller_arn="arn:aws:iam::123456789012:role/TestRole",
        )
        self.assertFalse(result)
        self.assertIn("Unexpected error", self.log_capture_handler.records[-1].message)

    def test_check_direct_prime_status_sts_client_error(self):
        self.mock_sts_client.get_caller_identity.side_effect = (
            botocore.exceptions.ClientError(
                {"Error": {"Code": "ExpiredToken", "Message": "Token expired"}},
                "GetCallerIdentity",
            )
        )
        result = _check_direct_prime_status("model", "us-east-1")
        self.assertFalse(result)
        self.assertIn(
            "Could not determine AWS Account ID/Caller ARN",
            self.log_capture_handler.records[-1].message,
        )


if __name__ == "__main__":
    unittest.main(argv=["first-arg-is-ignored"], exit=False)
