from unittest.mock import patch
import pytest

from sagemaker_jupyterlab_extension_common.jumpstart.stage_utils import (
    get_jumpstart_content_bucket,
    is_jumpstart_supported_region,
)


@pytest.mark.parametrize(
    "stage,region,expected",
    [
        ("devo", "us-west-2", "jumpstart-cache-beta-us-west-2"),
        ("prod", "us-east-1", "jumpstart-cache-prod-us-east-1"),
        ("loadtest", "us-east-1", "jumpstart-cache-beta-us-east-1"),
        ("predevo", "us-east-1", "jumpstart-cache-beta-us-east-1"),
    ],
)
def test_get_jumpstart_content_bucket(stage, region, expected):
    assert expected == get_jumpstart_content_bucket(stage, region)


@pytest.mark.parametrize(
    "stage,expected",
    [
        ("us-west-2", True),
        ("us-east-1", True),
        ("us-east-2", True),
        ("dummy-region", False),
        ("cn-north-1", True),
    ],
)
@patch("sagemaker_jupyterlab_extension_common.jumpstart.stage_utils.get_region_name")
def test_is_jumpstart_supported_region(
    get_region_name_mock,
    stage,
    expected,
):
    get_region_name_mock.return_value = stage
    assert expected == is_jumpstart_supported_region()
