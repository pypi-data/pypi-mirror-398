# Clients in this file do not use USE_DUALSTACK_ENDPOINT variable
# These clients will make IPv4 calls only, intended to make the first initial API calls to detect if dual stack is enabled
# This is to ensure there is no circular dependency during import time of .constant/USE_DUALSTACK_ENDPOINT
# Long term: This client will be deprecated in favor of environment variable to detect dual stack

import os
from typing import Optional
import botocore
import logging
import boto3

from sagemaker_jupyterlab_extension_common.exceptions import S3ObjectNotFoundError
from traitlets.config import SingletonConfigurable

from sagemaker_jupyterlab_extension_common.util.app_metadata import (
    get_region_name,
    get_stage,
    get_domain_id,
    get_partition,
    get_space_name,
)

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))

MAX_RETRY_ATEMPTS = 1
CONNECTION_TIMEOUT = 2  # seconds
READ_TIMEOUT = 20  # seconds

LOOSELEAF_STAGE_MAPPING = {"devo": "beta", "loadtest": "gamma"}


class BaseBoto3Client:
    cfg: any
    region_name: str
    partition: str
    sess: boto3.Session

    def __init__(self, region_name: str, partition: str, model_data_path=None):
        self.cfg = botocore.client.Config(
            connect_timeout=CONNECTION_TIMEOUT,
            read_timeout=READ_TIMEOUT,
            retries={"max_attempts": MAX_RETRY_ATEMPTS},
        )
        self.region_name = region_name
        self.partition = partition
        self.sess = boto3.Session()


class SageMakerBoto3Client(BaseBoto3Client, SingletonConfigurable):
    """
    A Singleton Class that provides a simple wrapper on sagemaker boto3 client.
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

        return self.sess.client(**create_client_args)

    def describe_domain(self, domain_id=None):
        try:
            domainId = self.default_domain_id if domain_id is None else domain_id
            sm_client = self._create_sagemaker_client()
            response = sm_client.describe_domain(DomainId=domainId)
        except botocore.exceptions.ClientError as error:
            logging.error(
                f"Failed to describe domain for domainId ({domainId}). {error.response}"
            )
            raise error
        return response


def get_sagemaker_client(create_new=False):
    """
    Returns the Sagemaker Client.
    create_new: boolean flag that allows to force-create a new instance for sagemaker client. Default is False
    """
    PACKAGE_ROOT = os.path.abspath(os.path.dirname(__file__))
    model_path = os.path.join(PACKAGE_ROOT, "botocore_model")

    if create_new:
        return SageMakerBoto3Client(get_region_name(), get_partition(), model_path)
    else:
        return SageMakerBoto3Client.instance(
            get_region_name(), get_partition(), model_path
        )
