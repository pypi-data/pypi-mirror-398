from sagemaker_jupyterlab_extension_common.jumpstart.constants import (
    JUMPSTART_GA_REGIONS,
)
from sagemaker_jupyterlab_extension_common.util.app_metadata import get_region_name


JUMPSTART_S3_BUCKET_SUBNAME = "jumpstart-cache"


def get_jumpstart_content_bucket(stage: str, region: str):
    """Map looseleaf stage to jumpstart content bucket"""
    if stage == "personal":
        stage = "alpha"
    if stage == "loadtest" or stage == "devo" or stage == "predevo":
        stage = "beta"
    else:
        stage = "prod"
    return f"{JUMPSTART_S3_BUCKET_SUBNAME}-{stage}-{region}"


def is_jumpstart_supported_region() -> bool:
    region = get_region_name()
    if region in JUMPSTART_GA_REGIONS:
        return True
    return False
