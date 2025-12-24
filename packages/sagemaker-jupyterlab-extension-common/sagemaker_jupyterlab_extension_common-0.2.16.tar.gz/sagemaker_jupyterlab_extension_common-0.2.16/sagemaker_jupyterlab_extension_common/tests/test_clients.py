import pytest
import asyncio
from typing import Dict
from unittest.mock import AsyncMock, Mock, MagicMock, patch, mock_open

from sagemaker_jupyterlab_extension_common.clients import (
    S3AsyncBoto3Client,
    SageMakerAsyncBoto3Client,
)


def mock_sagemaker_client(method_mock: Dict) -> (Mock, Mock):
    sagemaker_client = SageMakerAsyncBoto3Client("us-west-2", "aws")
    inner_client = Mock(**method_mock)
    sagemaker_client.sess = Mock(
        **{
            "create_client.return_value": MagicMock(
                **{"__aenter__.return_value": inner_client}
            )
        }
    )
    return sagemaker_client, inner_client


def mock_s3_client(method_mock: Dict) -> (Mock, Mock):
    s3_client = S3AsyncBoto3Client("us-west-2", "aws")
    inner_client = Mock(**method_mock)
    s3_client.sess = Mock(
        **{
            "create_client.return_value": MagicMock(
                **{"__aenter__.return_value": inner_client}
            )
        }
    )
    return s3_client, inner_client


def get_future_results(result):
    future = asyncio.Future()
    future.set_result(result)
    return future


DESCRIBE_DOMAIN_TEST_RESPONSE = {
    "DomainArn": "arn:aws:sagemaker:us-east-2:112233445566:domain/d-jhgjggjgmp",
    "DomainId": "d-jhgjggjgmp",
    "DomainName": "test-domain-pysdk",
    "HomeEfsFileSystemId": "fs-00112233445566",
    "Status": "InService",
    "CreationTime": 1688664545.612,
    "LastModifiedTime": 1690353623.767,
    "AuthMode": "IAM",
    "DefaultUserSettings": {
        "ExecutionRole": "arn:aws:iam::112233445566:role/service-role/AmazonSageMaker-ExecutionRole-112233445566",
        "SharingSettings": {
            "NotebookOutputOption": "Allowed",
            "S3OutputPath": "s3://sagemaker-studio-112211334455-mixlxni8rqb/sharing",
        },
        "JupyterServerAppSettings": {
            "DefaultResourceSpec": {
                "SageMakerImageArn": "arn:aws:sagemaker:us-east-2:112233445566:image/jupyter-server-3",
                "InstanceType": "system",
            },
            "CodeRepositories": [
                {"RepositoryUrl": "https://github.com/aws/sagemaker-python-sdk.git"}
            ],
        },
        "CanvasAppSettings": {
            "TimeSeriesForecastingSettings": {
                "Status": "ENABLED",
                "AmazonForecastRoleArn": "arn:aws:iam::112233445566:role/service-role/AmazonSagemakerCanvasForecastRole-112233445566",
            }
        },
    },
    "DefaultSpaceSettings": {
        "ExecutionRole": "arn:aws:iam::112233445566:role/service-role/AmazonSageMaker-ExecutionRole-112233445566"
    },
    "AppNetworkAccessType": "PublicInternetOnly",
    "SubnetIds": [
        "subnet-00000000000000000",
        "subnet-11111111111111111",
        "subnet-22222222222222222",
    ],
    "Url": "https://d-jhgjggjgmp.studio.us-east-2.sagemaker.aws",
    "VpcId": "vpc-1128jkhkhklk8",
}


DESCRIBE_USER_PROFILE_TEST_RESPONSE = {
    "ExecutionRole": "string",
    "SecurityGroups": [
        "string",
    ],
    "SharingSettings": {
        "NotebookOutputOption": "Allowed",
        "S3OutputPath": "string",
        "S3KmsKeyId": "string",
    },
    "JupyterServerAppSettings": {
        "DefaultResourceSpec": {
            "SageMakerImageArn": "string",
            "SageMakerImageVersionArn": "string",
            "InstanceType": "system",
            "LifecycleConfigArn": "string",
        },
        "LifecycleConfigArns": [
            "string",
        ],
        "CodeRepositories": [
            {"RepositoryUrl": "string"},
        ],
    },
}


DESCRIBE_SPACE_TEST_RESPONSE = {
    "DomainId": "d-1234567890",
    "SpaceArn": "arn:aws:someArn",
    "SpaceName": "default-test-space",
    "Status": "InService",
    "LastModifiedTime": "2023-09-25T23:53:53.469000+00:00",
    "CreationTime": "2023-09-25T23:53:41.245000+00:00",
    "SpaceSettings": {
        "AppType": "JupyterLab",
        "SpaceStorageSettings": {"EbsStorageSettings": {"EbsVolumeSizeInGb": 5}},
        "JupyterLabAppSettings": {
            "CodeRepositories": [
                {"RepositoryUrl": "https://github.com/space/space-repo.git"}
            ],
        },
    },
    "OwnershipSettings": {"OwnerUserProfileName": "default-test-user-profile"},
    "SpaceSharingSettings": {"SharingType": "Private"},
}

LIST_PROJECTS_TEST_RESPONSE = {
    "ProjectSummaryList": [
        {
            "CreationTime": 12345,
            "ProjectArn": "arn:test-project",
            "ProjectDescription": "test project",
            "ProjectId": "test-project",
            "ProjectName": "test-project",
            "ProjectStatus": "CreateCompleted",
        }
    ],
}


HEAD_OBJECT_TEST_RESPONSE = {
    "AcceptRanges": "bytes",
    "ContentLength": "3191",
    "ContentType": "image/jpeg",
    "ETag": '"6805f2cfc46c0f04559748bb039d69ae"',
    "Metadata": {},
    "VersionId": "null",
}


@pytest.mark.asyncio
@patch(
    "sagemaker_jupyterlab_extension_common.clients.get_stage",
    return_value="prod",
)
@patch(
    "sagemaker_jupyterlab_extension_common.clients.get_domain_id",
    return_value="test-domain-id",
)
@patch(
    "sagemaker_jupyterlab_extension_common.clients.get_space_name",
    return_value="test-space",
)
async def test_describe_domain_success(mock_space, mock_domain, mock_stage):
    # Given
    sagemaker_client, inner_client = mock_sagemaker_client(
        {
            "describe_domain.return_value": get_future_results(
                DESCRIBE_DOMAIN_TEST_RESPONSE
            )
        }
    )

    # When
    result = await sagemaker_client.describe_domain(domain_id="d-jfffdjjjvhy")

    # Then
    sagemaker_client.sess.create_client.assert_called_with(
        service_name="sagemaker",
        config=sagemaker_client.cfg,
        region_name="us-west-2",
    )
    inner_client.describe_domain.assert_called_with(DomainId="d-jfffdjjjvhy")
    assert result == DESCRIBE_DOMAIN_TEST_RESPONSE


@pytest.mark.asyncio
@patch(
    "sagemaker_jupyterlab_extension_common.clients.get_stage",
    return_value="prod",
)
@patch(
    "sagemaker_jupyterlab_extension_common.clients.get_domain_id",
    return_value="test-domain-id",
)
@patch(
    "sagemaker_jupyterlab_extension_common.clients.get_space_name",
    return_value="test-space",
)
async def test_describe_domain_called_with_default_domain_success(
    mock_space, mock_domain, mock_stage
):
    # Given
    sagemaker_client, inner_client = mock_sagemaker_client(
        {
            "describe_domain.return_value": get_future_results(
                DESCRIBE_DOMAIN_TEST_RESPONSE
            )
        }
    )

    # When
    result = await sagemaker_client.describe_domain()

    # Then
    sagemaker_client.sess.create_client.assert_called_with(
        service_name="sagemaker",
        config=sagemaker_client.cfg,
        region_name="us-west-2",
    )
    inner_client.describe_domain.assert_called_with(DomainId="test-domain-id")
    assert result == DESCRIBE_DOMAIN_TEST_RESPONSE


@pytest.mark.asyncio
@patch(
    "sagemaker_jupyterlab_extension_common.clients.get_stage",
    return_value="prod",
)
@patch(
    "sagemaker_jupyterlab_extension_common.clients.get_domain_id",
    return_value="test-domain-id",
)
@patch(
    "sagemaker_jupyterlab_extension_common.clients.get_space_name",
    return_value="test-space",
)
async def test_describe_user_profile_success(mock_space, mock_domain, mock_stage):
    # Given
    sagemaker_client, inner_client = mock_sagemaker_client(
        {
            "describe_user_profile.return_value": get_future_results(
                DESCRIBE_USER_PROFILE_TEST_RESPONSE
            )
        }
    )

    # When
    result = await sagemaker_client.describe_user_profile(
        domain_id="d-jfffdjjjvhy", user_profile_name="user-jjkk1122ll"
    )

    # Then
    sagemaker_client.sess.create_client.assert_called_with(
        service_name="sagemaker",
        config=sagemaker_client.cfg,
        region_name="us-west-2",
    )
    inner_client.describe_user_profile.assert_called_with(
        DomainId="d-jfffdjjjvhy", UserProfileName="user-jjkk1122ll"
    )
    assert result == DESCRIBE_USER_PROFILE_TEST_RESPONSE


@pytest.mark.asyncio
@patch(
    "sagemaker_jupyterlab_extension_common.clients.get_stage",
    return_value="devo",
)
@patch(
    "sagemaker_jupyterlab_extension_common.clients.get_domain_id",
    return_value="test-domain-id",
)
@patch(
    "sagemaker_jupyterlab_extension_common.clients.get_space_name",
    return_value="test-space",
)
async def test_create_sagemaker_client_with_devo_stage(
    mock_space, mock_domain, mock_stage
):
    sagemaker_client, inner_client = mock_sagemaker_client(
        {
            "describe_domain.return_value": get_future_results(
                DESCRIBE_DOMAIN_TEST_RESPONSE
            )
        }
    )

    # any call to sagemaker should use the correct endpoint
    result = await sagemaker_client.describe_domain(domain_id="d-jfffdjjjvhy")

    sagemaker_client.sess.create_client.assert_called_with(
        service_name="sagemaker",
        config=sagemaker_client.cfg,
        region_name="us-west-2",
        endpoint_url=f"https://sagemaker.beta.us-west-2.ml-platform.aws.a2z.com",
    )


@pytest.mark.asyncio
@patch(
    "sagemaker_jupyterlab_extension_common.clients.get_stage",
    return_value="prod",
)
@patch(
    "sagemaker_jupyterlab_extension_common.clients.get_domain_id",
    return_value="default_domain",
)
@patch(
    "sagemaker_jupyterlab_extension_common.clients.get_space_name",
    return_value="default_test_space",
)
async def test_describe_space_with_default_space_name_success(
    mock_space, mock_domain, mock_stage
):
    # Given
    sagemaker_client, inner_client = mock_sagemaker_client(
        {
            "describe_space.return_value": get_future_results(
                DESCRIBE_SPACE_TEST_RESPONSE
            )
        }
    )

    # When
    result = await sagemaker_client.describe_space()

    # Then
    sagemaker_client.sess.create_client.assert_called_with(
        service_name="sagemaker",
        config=sagemaker_client.cfg,
        region_name="us-west-2",
    )
    inner_client.describe_space.assert_called_with(
        DomainId="default_domain", SpaceName="default_test_space"
    )
    assert result == DESCRIBE_SPACE_TEST_RESPONSE


@pytest.mark.asyncio
async def test_list_projects_success():
    # Given
    sagemaker_client, inner_client = mock_sagemaker_client(
        {"list_projects.return_value": get_future_results(LIST_PROJECTS_TEST_RESPONSE)}
    )

    # When
    result = await sagemaker_client.list_projects()

    # Then
    sagemaker_client.sess.create_client.assert_called_with(
        service_name="sagemaker",
        config=sagemaker_client.cfg,
        region_name="us-west-2",
    )
    assert result == LIST_PROJECTS_TEST_RESPONSE


@pytest.mark.asyncio
async def test_s3_client_get_object():
    mock_response = {
        "Body": MagicMock(
            **{
                "__aenter__.return_value": Mock(
                    **{"read.return_value": get_future_results(b"my test data")}
                )
            }
        )
    }
    # Given
    s3_client, inner_client = mock_s3_client(
        {"get_object.return_value": get_future_results(mock_response)}
    )
    # When
    result = await s3_client.get_object("mock_bucket", "mock_key")
    # Then
    s3_client.sess.create_client.assert_called_with(
        service_name="s3",
        config=s3_client.cfg,
        region_name="us-west-2",
    )
    inner_client.get_object.assert_called_with(Bucket="mock_bucket", Key="mock_key")
    assert result == b"my test data"


@pytest.mark.asyncio
async def test_s3_client_head_object():
    # Given
    s3_client, inner_client = mock_s3_client(
        {"head_object.return_value": get_future_results(HEAD_OBJECT_TEST_RESPONSE)}
    )
    # When
    result = await s3_client.head_object("mock_bucket", "mock_key")
    # Then
    s3_client.sess.create_client.assert_called_with(
        service_name="s3",
        config=s3_client.cfg,
        region_name="us-west-2",
    )
    inner_client.head_object.assert_called_with(Bucket="mock_bucket", Key="mock_key")
    assert result == HEAD_OBJECT_TEST_RESPONSE
