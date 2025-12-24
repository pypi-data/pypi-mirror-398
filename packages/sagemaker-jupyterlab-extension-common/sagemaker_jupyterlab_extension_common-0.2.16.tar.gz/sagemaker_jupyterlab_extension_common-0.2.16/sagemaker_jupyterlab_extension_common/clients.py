import os
from typing import Optional
import botocore
import logging

from sagemaker_jupyterlab_extension_common.exceptions import S3ObjectNotFoundError

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))

from aiobotocore.session import get_session, AioSession
from traitlets.config import SingletonConfigurable

from sagemaker_jupyterlab_extension_common.util.app_metadata import (
    get_region_name,
    get_stage,
    get_domain_id,
    get_partition,
    get_space_name,
)
from sagemaker_jupyterlab_extension_common.constants import USE_DUALSTACK_ENDPOINT

# Values currently set to match LooseLeafNb2Kg
MAX_RETRY_ATEMPTS = 2
CONNECTION_TIMEOUT = 10  # seconds
READ_TIMEOUT = 20  # seconds

LOOSELEAF_STAGE_MAPPING = {"devo": "beta", "loadtest": "gamma"}


class BaseAysncBoto3Client:
    cfg: any
    region_name: str
    partition: str
    sess: AioSession

    def __init__(self, region_name: str, partition: str, model_data_path=None):
        self.cfg = botocore.client.Config(
            connect_timeout=CONNECTION_TIMEOUT,
            read_timeout=READ_TIMEOUT,
            retries={"max_attempts": MAX_RETRY_ATEMPTS},
            use_dualstack_endpoint=USE_DUALSTACK_ENDPOINT,
        )
        self.region_name = region_name
        self.partition = partition
        # This allows us to load any additional service model files. That could allows us to have private service clients or desired methods.
        # https://botocore.amazonaws.com/v1/documentation/api/latest/reference/loaders.html
        # This does not imapct any other clients created or running in environemnt,
        if model_data_path is not None:
            self.sess = get_session(
                env_vars={"data_path": (None, None, model_data_path, None)}
            )
        else:
            self.sess = get_session()


class S3AsyncBoto3Client(BaseAysncBoto3Client, SingletonConfigurable):
    """This class is a Singleton that provides a simple async wrapper on s3 boto3 client.
    This wrapper class uses aiobotocore, a library that provides async client to aws services.
    """

    def __init__(self, region_name, partition_name, model_data_path=None):
        super().__init__(region_name, partition_name, model_data_path)

    def _create_s3_client(self):
        create_client_args = {
            "service_name": "s3",
            "config": self.cfg,
            "region_name": self.region_name,
        }
        return self.sess.create_client(**create_client_args)

    async def get_object(
        self, bucket: str, key: str, expected_bucket_owner: Optional[str] = None
    ) -> bytes:
        try:
            async with self._create_s3_client() as s3_client:
                if expected_bucket_owner is not None:
                    response = await s3_client.get_object(
                        Bucket=bucket,
                        Key=key,
                        ExpectedBucketOwner=expected_bucket_owner,
                    )
                else:
                    response = await s3_client.get_object(Bucket=bucket, Key=key)
                async with response["Body"] as stream:
                    content = await stream.read()
        except botocore.exceptions.ClientError as error:
            logging.error(f"Failed to get s3 object. {error.response}")
            raise
        return content

    async def head_object(
        self, bucket: str, key: str, expected_bucket_owner: Optional[str] = None
    ) -> dict:
        try:
            async with self._create_s3_client() as s3_client:
                if expected_bucket_owner is not None:
                    response = await s3_client.head_object(
                        Bucket=bucket,
                        Key=key,
                        ExpectedBucketOwner=expected_bucket_owner,
                    )
                else:
                    response = await s3_client.head_object(Bucket=bucket, Key=key)
        except botocore.exceptions.ClientError as error:
            if error.response["Error"]["Code"] == "404":
                raise S3ObjectNotFoundError(
                    f"Object does not exist. bucket: {bucket}, key: {key}"
                )
            else:
                raise
        return response


class SageMakerAsyncBoto3Client(BaseAysncBoto3Client, SingletonConfigurable):
    """
    A Singleton Class that provides a simple async wrapper on sagemaker boto3 client.
    This wrapper class uses aiobotocore, a library that provides async client to aws services.
    """

    def __init__(
        self,
        region_name: str,
        partition_name: str,
        model_data_path: Optional[str] = None,
    ):
        super().__init__(region_name, partition_name, model_data_path)
        self.default_domain_id = get_domain_id()
        self.default_space_name = get_space_name()

    def _create_sagemaker_client(self):
        stage = get_stage()

        create_client_args = {
            "service_name": "sagemaker",
            "config": self.cfg,
            "region_name": self.region_name,
        }
        if stage is not None and stage != "" and stage.lower() != "prod":
            endpoint_stage = LOOSELEAF_STAGE_MAPPING[stage.lower()]
            create_client_args["endpoint_url"] = (
                f"https://sagemaker.{endpoint_stage}.{self.region_name}.ml-platform.aws.a2z.com"
            )

        return self.sess.create_client(**create_client_args)

    async def describe_domain(self, domain_id=None):
        try:
            domainId = self.default_domain_id if domain_id is None else domain_id
            logging.info(f"Received request to describe domain with Id - ({domainId})")
            async with self._create_sagemaker_client() as sm_client:
                response = await sm_client.describe_domain(DomainId=domainId)
                logging.info(f"Successfuly described domain with Id: ({domainId})")
        except botocore.exceptions.ClientError as error:
            logging.error(
                f"Failed to describe domain for domainId ({domainId}). {error.response}"
            )
            raise error
        return response

    async def describe_user_profile(self, domain_id=None, user_profile_name=None):
        try:
            domainId = self.default_domain_id if domain_id is None else domain_id
            logging.info(
                f"Received request to describe user-profile with DomainId ({domainId}) and profile-name ({user_profile_name}) "
            )
            async with self._create_sagemaker_client() as sm_client:
                response = await sm_client.describe_user_profile(
                    DomainId=domainId, UserProfileName=user_profile_name
                )
                logging.info(
                    f"Successfuly described user-profile ({user_profile_name}) in domain with Id ({domainId})"
                )
        except botocore.exceptions.ClientError as error:
            logging.error(
                f"Failed to describe user-profile ({user_profile_name}) in domain ({domainId}). {error.response}"
            )
            raise error
        return response

    async def describe_space(self, domain_id=None, space_name=None):
        try:
            domainId = self.default_domain_id if domain_id is None else domain_id
            spaceName = self.default_space_name if space_name is None else space_name
            logging.info(
                f"Received request to describe space with DomainId ({domainId}) and space-name ({spaceName}) "
            )
            async with self._create_sagemaker_client() as sm_client:
                response = await sm_client.describe_space(
                    DomainId=domainId, SpaceName=spaceName
                )
                logging.info(
                    f"Successfuly described space ({spaceName}) in domain with Id ({domainId})"
                )
        except botocore.exceptions.ClientError as error:
            logging.error(
                f"Failed to describe space ({spaceName}) in domain ({domainId}). {error.response}"
            )
            raise error
        return response

    async def list_projects(self):
        projects = []
        next_token = None
        try:
            logging.info(f"Received request to list projects")
            async with self._create_sagemaker_client() as sm_client:
                while True:
                    params = {}
                    if next_token:
                        params["NextToken"] = next_token
                    response = await sm_client.list_projects(**params)
                    projects.extend(response.get("ProjectSummaryList", []))
                    next_token = response.get("NextToken")
                    if not next_token:
                        break
                logging.info(f"Successfuly listed projects")
        except botocore.exceptions.ClientError as error:
            logging.error(f"Failed to list projects")
            raise error
        return {"ProjectSummaryList": projects}


"""
    Returns the Sagemaker Client.
    create_new: boolean flag that allows to force-create a new instance for sagemaker client. Default is False
"""


def get_sagemaker_client(create_new=False):
    PACKAGE_ROOT = os.path.abspath(os.path.dirname(__file__))
    model_path = os.path.join(PACKAGE_ROOT, "botocore_model")

    if create_new:
        return SageMakerAsyncBoto3Client(get_region_name(), get_partition(), model_path)
    else:
        return SageMakerAsyncBoto3Client.instance(
            get_region_name(), get_partition(), model_path
        )


"""
    Returns the S3 Client.
    create_new: boolean flag that allows to force-create a new instance for s3 client. Default is False
"""


def get_s3_client(create_new=False):
    if create_new:
        return S3AsyncBoto3Client(get_region_name(), get_partition())
    else:
        return S3AsyncBoto3Client.instance(get_region_name(), get_partition())
