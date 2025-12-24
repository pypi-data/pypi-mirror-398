import re
import contextvars
from pydantic.v1 import (
    BaseModel,
    ConfigDict,
    Field,
    validator,
)
from typing import Optional

from sagemaker_jupyterlab_extension_common.jumpstart.constants import (
    MISSING_CLIENT_REQUEST_ID,
    MISSING_SERVER_REQUEST_ID,
)

from sagemaker_jupyterlab_extension_common.jumpstart.notebook_types import (
    JumpStartResourceType,
)

client_request_id_var = contextvars.ContextVar(
    "client_request_id", default=MISSING_CLIENT_REQUEST_ID
)
server_request_id_var = contextvars.ContextVar(
    "server_request_id", default=MISSING_SERVER_REQUEST_ID
)


class NotebookRequest(BaseModel):
    """
    Request model for JumpStart notebook operations with multi-layer validation.

    Validation Flow (executed in order):
    1. Root Validator (sanitize_all_strings) - Runs first with pre=True
       - Applies default regex to string fields without explicit regex
       - Blocks: quotes, semicolons, spaces, parentheses, shell metacharacters
       - Skips: non-string fields and fields with explicit regex

    2. Field-Level Regex - Runs second
       - Validates format/pattern for fields with explicit regex parameter
       - Each field can have specific validation rules (e.g., AWS naming conventions)
       - Blocks malicious input before it reaches custom validators

    3. Custom Validators - Runs last
       - Enforces business logic and conditional requirements
       - Only executes if field-level validation passes
    """

    key: str = Field(
        regex=r"^[a-zA-Z0-9\-_./]+\.ipynb$",
        max_length=1024,
        min_length=1,
    )
    resource_type: JumpStartResourceType = JumpStartResourceType.default
    # use js_model_id because `model_` is a reserved namespace in pydantic
    js_model_id: Optional[str] = Field(
        default=None,
        max_length=256,
        validate_default=True,
        regex=r"^[a-zA-Z0-9\-]+$",
        alias="model_id",
    )
    cluster_id: Optional[str] = Field(
        max_length=256,
        regex=r"^[a-zA-Z0-9\-_]+$",
        default=None,
    )
    connection_id: Optional[str] = Field(
        max_length=256,
        regex=r"^[a-zA-Z0-9\-_]+$",
        default=None,
    )
    domain: Optional[str] = Field(
        max_length=256,
        regex=r"^[a-zA-Z0-9\-]+$",
        default=None,
    )
    endpoint_name: Optional[str] = Field(
        default=None,
        max_length=63,
        regex=r"^[a-zA-Z0-9]([\-a-zA-Z0-9]*[a-zA-Z0-9])?$",
        validate_default=True,
    )
    inference_component: Optional[str] = Field(
        default=None,
        max_length=63,
        regex=r"^[a-zA-Z0-9](-*[a-zA-Z0-9]){0,62}$",
        validate_default=True,
    )
    set_default_kernel: Optional[bool] = Field(
        default=False,
    )

    model_config = ConfigDict(frozen=True, strict=True)

    hub_name: Optional[str] = Field(
        default=None,
        max_length=63,
        regex=r"^[a-zA-Z0-9](-*[a-zA-Z0-9]){0,62}$",
    )

    recipe_path: Optional[str] = Field(
        default=None, max_length=256, regex=r"^(?:/?)[a-zA-Z0-9_\-./]+$"
    )

    base_model_name: Optional[str] = Field(
        default=None, max_length=128, regex=r"^[a-zA-Z0-9\-._]+$"
    )

    customization_technique: Optional[str] = Field(
        default=None, max_length=32, regex=r"^[a-zA-Z0-9\-._]+$"
    )

    model_package_group_name: Optional[str] = Field(
        default=None, max_length=128, regex=r"^[a-zA-Z0-9\-._]+$"
    )

    data_set_name: Optional[str] = Field(
        default=None, max_length=128, regex=r"^[a-zA-Z0-9\-._]+$"
    )

    data_set_version: Optional[str] = Field(
        default=None, max_length=32, regex=r"^[a-zA-Z0-9\-._]+$"
    )

    # Root validator for default sanitization of all string parameters
    @validator("*", pre=True)
    @classmethod
    def sanitize_all_strings(cls, v, field):
        """Apply default sanitization to string fields without explicit regex."""
        if not isinstance(v, str):
            return v

        # Skip fields that already have explicit regex validation
        field_info = cls.__fields__.get(field.name)
        if field_info and field_info.field_info.regex:
            return v

        # Apply default sanitization for fields without regex
        if not re.match(r"^[a-zA-Z0-9\-_./]+$", v):
            raise ValueError(
                f"{field.name}: contains invalid characters. "
                f"Only alphanumeric, hyphens, underscores, dots, and slashes allowed."
            )

        return v

    # Conditional validation for model_id
    @validator("js_model_id", always=True)
    @classmethod
    def check_model_id(cls, model_id: str, values: dict) -> str:
        if (
            values.get("resource_type") == JumpStartResourceType.modelSdkNotebook
            and not model_id
        ):
            raise ValueError(
                "model_id is required when resource_type is modelSdkNotebook"
            )
        return model_id

    # Conditional validation for endpoint_name
    @validator("endpoint_name", always=True)
    @classmethod
    def check_endpoint_name(cls, endpoint_name: str, values: dict) -> str:
        if (
            values.get("resource_type") == JumpStartResourceType.inferNotebook
            and not endpoint_name
        ):
            raise ValueError(
                f"endpoint_name is required when resource_type is inferNotebook"
            )
        return endpoint_name

    # Conditional validation for recipe_path
    @validator("recipe_path", always=True)
    @classmethod
    def check_nova_notebook_recipe_path(cls, recipe_path: str, values: dict) -> str:
        RECIPE_PATH_REGEX = re.compile(
            r"^/recipes/([a-zA-Z0-9_\-]+)/([a-zA-Z0-9_\-]+)/([a-zA-Z0-9_\-]+)\.yaml$"
        )
        if values.get("resource_type") == JumpStartResourceType.novaNotebook:
            if not recipe_path:
                raise ValueError(
                    f"recipe_path is required when resource_type is novaNotebook"
                )

            # Apply the strict regex validation
            match = RECIPE_PATH_REGEX.match(recipe_path)
            if not match:
                raise ValueError(
                    f"recipe_path: '{recipe_path}' does not conform to the expected recipe path format"
                )
        return recipe_path

    # Validation for customization_technique
    @validator("customization_technique", always=True)
    @classmethod
    def validate_customization_technique(cls, technique: str) -> str:
        from sagemaker_jupyterlab_extension_common.jumpstart.constants import (
            SUPPORTED_CUSTOMIZATION_TECHNIQUES,
        )

        if technique and technique not in SUPPORTED_CUSTOMIZATION_TECHNIQUES:
            supported = ", ".join(SUPPORTED_CUSTOMIZATION_TECHNIQUES)
            raise ValueError(
                f"Unsupported customization technique '{technique}'. Supported: {supported}"
            )
        return technique
