import pytest
from unittest.mock import patch, mock_open, Mock

from sagemaker_jupyterlab_extension_common.dual_stack_utils import is_dual_stack_enabled


@patch("builtins.open", new_callable=mock_open, read_data='{"DomainId": "d-test123"}')
@patch("sagemaker_jupyterlab_extension_common.dual_stack_utils.get_sagemaker_client")
def test_is_dual_stack_enabled_dualstack(mock_get_client, mock_file):
    mock_client = Mock()
    mock_client.describe_domain.return_value = {
        "DomainSettings": {"IpAddressType": "DualStack"}
    }
    mock_get_client.return_value = mock_client

    result = is_dual_stack_enabled()

    assert result is True
    mock_client.describe_domain.assert_called_once_with("d-test123")


@patch("builtins.open", new_callable=mock_open, read_data='{"DomainId": "d-test123"}')
@patch("sagemaker_jupyterlab_extension_common.dual_stack_utils.get_sagemaker_client")
def test_is_dual_stack_enabled_ipv4_only(mock_get_client, mock_file):
    mock_client = Mock()
    mock_client.describe_domain.return_value = {
        "DomainSettings": {"IpAddressType": "Ipv4Only"}
    }
    mock_get_client.return_value = mock_client

    result = is_dual_stack_enabled()
    assert result is False


@patch("builtins.open", new_callable=mock_open, read_data='{"DomainId": "d-test123"}')
@patch("sagemaker_jupyterlab_extension_common.dual_stack_utils.get_sagemaker_client")
def test_is_dual_stack_enabled_missing_domain_settings(mock_get_client, mock_file):
    mock_client = Mock()
    mock_client.describe_domain.return_value = {}
    mock_get_client.return_value = mock_client

    result = is_dual_stack_enabled()
    assert result is False


@patch("builtins.open", new_callable=mock_open, read_data='{"DomainId": "d-test123"}')
@patch("sagemaker_jupyterlab_extension_common.dual_stack_utils.get_sagemaker_client")
def test_is_dual_stack_enabled_invalid_ip_address_type(mock_get_client, mock_file):
    mock_client = Mock()
    mock_client.describe_domain.return_value = {
        "DomainSettings": {"IpAddressType": 123}
    }
    mock_get_client.return_value = mock_client

    result = is_dual_stack_enabled()
    assert result is False


@patch("builtins.open", new_callable=mock_open, read_data='{"DomainId": "d-test123"}')
@patch("sagemaker_jupyterlab_extension_common.dual_stack_utils.get_sagemaker_client")
def test_is_dual_stack_enabled_none_domain_details(mock_get_client, mock_file):
    mock_client = Mock()
    mock_client.describe_domain.return_value = None
    mock_get_client.return_value = mock_client

    result = is_dual_stack_enabled()
    assert result is False


@patch("builtins.open", side_effect=FileNotFoundError())
def test_is_dual_stack_enabled_file_not_found(mock_file):
    result = is_dual_stack_enabled()
    assert result is False


@patch("builtins.open", new_callable=mock_open, read_data="invalid json")
def test_is_dual_stack_enabled_invalid_json(mock_file):
    result = is_dual_stack_enabled()
    assert result is False


@patch("builtins.open", new_callable=mock_open, read_data='{"OtherKey": "value"}')
def test_is_dual_stack_enabled_missing_domain_id(mock_file):
    result = is_dual_stack_enabled()
    assert result is False


@patch("builtins.open", new_callable=mock_open, read_data='{"DomainId": "d-test123"}')
@patch("sagemaker_jupyterlab_extension_common.dual_stack_utils.get_sagemaker_client")
def test_is_dual_stack_enabled_client_exception(mock_get_client, mock_file):
    mock_client = Mock()
    mock_client.describe_domain.side_effect = Exception("API Error")
    mock_get_client.return_value = mock_client

    result = is_dual_stack_enabled()
    assert result is False
