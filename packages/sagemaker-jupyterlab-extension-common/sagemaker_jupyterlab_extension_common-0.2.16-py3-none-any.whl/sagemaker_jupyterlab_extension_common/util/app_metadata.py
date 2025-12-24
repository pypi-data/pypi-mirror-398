import os
from functools import lru_cache
import logging

from botocore.session import Session

SAGEMAKER_INTERNAL_METADATA_FILE_PATH = "/opt/.sagemakerinternal/internal-metadata.json"
METADATA_FILE_PATH = os.environ.get(
    "RESOURCE_METADATA_FILE", "/opt/ml/metadata/resource-metadata.json"
)
METADATA_DIR = os.environ.get("METADATA_DIR", "/opt/.sagemakerinternal")


from sagemaker_jupyterlab_extension_common.util.file_watcher import (
    WatchedJsonFile,
)

_watched_resource_metadata_file = WatchedJsonFile(METADATA_FILE_PATH, logging)
_watched_internal_metadata_file = WatchedJsonFile(
    SAGEMAKER_INTERNAL_METADATA_FILE_PATH, logging
)


@lru_cache(maxsize=1)
def get_region_name():
    region = os.environ.get("AWS_REGION")
    if region is not None:
        return region
    else:
        return get_default_aws_region()


@lru_cache(maxsize=1)
def get_default_aws_region():
    return os.environ.get("AWS_DEFAULT_REGION", "us-west-2")


@lru_cache(maxsize=1)
def get_aws_account_id():
    account_id = os.environ.get("AWS_ACCOUNT_ID")
    if account_id:
        return account_id
    execution_role_arn = _watched_resource_metadata_file.get_key("ExecutionRoleArn")
    if execution_role_arn:
        try:
            return execution_role_arn.split(":")[4]
        except (IndexError, AttributeError):
            pass
    return "MISSING_AWS_ACCOUNT_ID"


@lru_cache(maxsize=1)
def get_domain_id():
    return _watched_resource_metadata_file.get_key("DomainId", "MISSING_DOMAIN_ID")


@lru_cache(maxsize=1)
def get_user_profile_name():
    return _watched_resource_metadata_file.get_key(
        "UserProfileName", "MISSING_DOMAIN_ID"
    )


@lru_cache(maxsize=1)
def get_stage():
    return _watched_internal_metadata_file.get_key("Stage")


def get_partition():
    return Session().get_partition_for_region(get_region_name())


@lru_cache(maxsize=1)
def get_space_name():
    return _watched_resource_metadata_file.get_key("SpaceName", "MISSING_SPACE_NAME")
