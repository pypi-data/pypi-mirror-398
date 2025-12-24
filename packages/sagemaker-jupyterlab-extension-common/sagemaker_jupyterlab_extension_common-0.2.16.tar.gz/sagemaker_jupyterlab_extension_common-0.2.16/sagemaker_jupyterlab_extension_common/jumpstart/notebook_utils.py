from collections.abc import Callable
import json
from pathlib import Path
from typing import Any, Literal, Optional

from async_lru import alru_cache
from sagemaker_jupyterlab_extension_common.clients import get_s3_client
from sagemaker_jupyterlab_extension_common.exceptions import (
    DownloadDirectoryNotFoundError,
    NotebookTooLargeError,
    ProjectStorageMetadataJsonDecodeError,
    SageMakerUnifiedStudioProjectDirectoryInvalidError,
    SageMakerUnifiedStudioProjectDirectoryNotSetError,
    SageMakerUnifiedStudioStorageMetadataFileNotFoundError,
)
from sagemaker_jupyterlab_extension_common.jumpstart.constants import (
    HOME_PATH,
    MD_NOTEBOOK_PATH,
    MD_PATH,
    MD_UNIFIED_STORAGE_NOTEBOOK_PATH,
    MD_UNIFIED_STORAGE_PATH,
    NOTEBOOK_PATH,
    NOTEBOOK_SIZE_LIMIT_IN_BYTES,
    NOTEBOOK_TRANSFORMATION_TYPE,
)
from sagemaker_jupyterlab_extension_common.jumpstart.notebook_types import (
    JumpStartModelNotebookSuffix,
    JumpStartResourceType,
)
from sagemaker_jupyterlab_extension_common.jumpstart.stage_utils import (
    get_jumpstart_content_bucket,
)
from sagemaker_jupyterlab_extension_common.util.app_metadata import (
    get_region_name,
    get_stage,
)


def get_jumpstart_notebook_name(
    model_id: Optional[str], key: str, resource_type: JumpStartResourceType
) -> str:
    """Generate jumpstart notebook file name based on model_id or key and resource_type.

    If model_id is provided, it will be used as the prefix of the file name.
    Otherwise, the s3 key will be used.
    Args:
        model_id (str): model id
        key (str): s3 key
        resource_type (JumpStartResourceType): resource type
    Returns:
        str: jumpstart notebook's file name.
    """
    notebook_suffix = get_jumpstart_notebook_suffix(resource_type)
    if not model_id:
        file_name = key.split("/")[-1]
        if file_name:
            file_name = file_name.split(".")[0]
            return f"{file_name}_{notebook_suffix}"

    return f"{model_id}_{notebook_suffix}"


def get_jumpstart_notebook_suffix(resource_type: JumpStartResourceType) -> str:
    if resource_type == JumpStartResourceType.inferNotebook:
        return JumpStartModelNotebookSuffix.inferNotebook.value
    elif resource_type == JumpStartResourceType.modelSdkNotebook:
        return JumpStartModelNotebookSuffix.modelSdkNotebook.value
    elif resource_type == JumpStartResourceType.proprietaryNotebook:
        return JumpStartModelNotebookSuffix.proprietaryNotebook.value
    return "nb"


def notebook_transformation_needed(resource_type: JumpStartResourceType) -> bool:
    return resource_type in NOTEBOOK_TRANSFORMATION_TYPE


def is_valid_notebook_resource_type(resource_type: str) -> bool:
    return any(resource.value == resource_type for resource in JumpStartResourceType)


@alru_cache(maxsize=5, ttl=60)
async def _get_object_size(bucket: str, key: str) -> Optional[int]:
    response = await get_s3_client().head_object(bucket, key)
    return response.get("ContentLength")


@alru_cache(maxsize=5, ttl=60)
async def _get_notebook_content(key: str) -> str:
    stage, region = get_stage(), get_region_name()
    bucket = get_jumpstart_content_bucket(stage, region)
    object_size = await _get_object_size(bucket, key)
    if not object_size or object_size > NOTEBOOK_SIZE_LIMIT_IN_BYTES:
        raise NotebookTooLargeError(f"Object {key} is too large to fit into memory")
    response = await get_s3_client().get_object(bucket, key)
    content = response.decode("UTF-8")
    return content


def read_project_dir_name_from_json_file(
    file_path: str,
    get_project_dir_name_enclosing_object: Callable[[Any], str],
    project_dir_name_key: str,
) -> str:
    """
    Given a json file, read the project dir name from it

    Args:
        get_project_dir_name_enclosing_object: This gets the result of json.load() as a first argument.
            We inject this because JSON can have arbitrary nesting, so reading from different
            JSON structures need to be specified by the caller.
            `(json_load_result) -> json_object_containing_project_dir_field`
    """
    SMUS_PROJECT_DIR_PATH_FALLBACK = ""

    try:
        with Path(file_path).open(mode="r", encoding="utf-8") as fp:
            resource_metadata = json.load(fp)
            smus_project_dir_path = get_project_dir_name_enclosing_object(
                resource_metadata
            ).get(
                project_dir_name_key,
                SMUS_PROJECT_DIR_PATH_FALLBACK,
            )

        if smus_project_dir_path == SMUS_PROJECT_DIR_PATH_FALLBACK:
            raise SageMakerUnifiedStudioProjectDirectoryNotSetError(
                f"{project_dir_name_key} metadata is missing from {file_path}."
            )

        smus_project_dir_name = Path(smus_project_dir_path).name

        if smus_project_dir_name not in ["src", "shared"]:
            raise SageMakerUnifiedStudioProjectDirectoryInvalidError(
                f"{smus_project_dir_path} is not a valid project directory path."
            )

        return smus_project_dir_name
    except json.JSONDecodeError as exc:
        raise ProjectStorageMetadataJsonDecodeError(
            f"There is an error reading the json in {file_path}. {exc}"
        )


def is_project_dir_name_key_present(
    file_path: str, validate_key_exists: Callable[[Any], bool]
):
    """
    Arguments
        file_path: The path where the resource_metadata JSON file lives.
        validate_key_exists: Given the resource_metadata JSON file, supply
            a validation function that checks if the key exists or not.
            ```python
            def validate_key_exists(resource_metadata) -> bool:
                return result
            ```
    """
    try:
        with Path(file_path).open(mode="r", encoding="utf-8") as fp:
            resource_metadata = json.load(fp)

            return validate_key_exists(resource_metadata)
    except json.JSONDecodeError as exc:
        raise ProjectStorageMetadataJsonDecodeError(
            f"There is an error reading the json in {file_path}. {exc}"
        )


def get_smus_project_dir_name() -> Literal["src", "shared"]:
    """
    Gets the SMUS project directory name, depending on the project storage type (Git or S3).

    Rationale: https://tiny.amazon.com/ls8y2q2s/rationale
    """
    RESOURCE_METADATA_FILE_PATH = "/opt/ml/metadata/resource-metadata.json"
    RESOURCE_METADATA_FILE_PATH_FIRST_LEVEL_KEY = "AdditionalMetadata"
    RESOURCE_METADATA_FILE_PATH_PROJECT_DIR_KEY = "ProjectSharedDirectory"

    SMUS_PROJECT_DIRECTORY_FILE_PATH = (
        f"{Path.home()}/.config/smus-storage-metadata.json"
    )

    if Path(RESOURCE_METADATA_FILE_PATH).exists():
        project_dir_name_key_exists = is_project_dir_name_key_present(
            file_path=RESOURCE_METADATA_FILE_PATH,
            validate_key_exists=lambda json_obj: RESOURCE_METADATA_FILE_PATH_PROJECT_DIR_KEY
            in json_obj.get(RESOURCE_METADATA_FILE_PATH_FIRST_LEVEL_KEY, {}),
        )

        if project_dir_name_key_exists:
            return read_project_dir_name_from_json_file(
                file_path=RESOURCE_METADATA_FILE_PATH,
                get_project_dir_name_enclosing_object=lambda json_load_result: json_load_result.get(
                    RESOURCE_METADATA_FILE_PATH_FIRST_LEVEL_KEY, {}
                ),
                project_dir_name_key=RESOURCE_METADATA_FILE_PATH_PROJECT_DIR_KEY,
            )

    if Path(SMUS_PROJECT_DIRECTORY_FILE_PATH).exists():
        return read_project_dir_name_from_json_file(
            file_path=SMUS_PROJECT_DIRECTORY_FILE_PATH,
            get_project_dir_name_enclosing_object=lambda json_load_result: json_load_result,
            project_dir_name_key="smusProjectDirectory",
        )

    raise SageMakerUnifiedStudioStorageMetadataFileNotFoundError(
        f"{SMUS_PROJECT_DIRECTORY_FILE_PATH} cannot be found."
    )


def validate_and_get_download_directory(
    home_path: str,
    target_download_dir: str,
    target_download_dir_full_path: str,
) -> str:
    """
    Check if target_download_dir exists before returning full path
    """
    if Path(home_path).joinpath(target_download_dir).is_dir():
        return target_download_dir_full_path
    raise DownloadDirectoryNotFoundError(
        f"{target_download_dir} not found in {home_path}"
    )


def generate_notebook_download_path(is_md_environment: bool) -> str:
    """
    Get the notebook download path based on the Studio environment
    (SMUS or non-SMUS) and project storage type (Git or S3).

    Raises:
        DownloadDirectoryNotFoundError: When the download directory containing the
            path doesn't exist.
        SageMakerUnifiedStudioStorageMetadataFileNotFoundError: When the metadata
            file containing the project directory location doesn't exist.
        SageMakerUnifiedStudioProjectDirectoryNotSetError: When the project directory
            location in the metadata file is empty.
        SageMakerUnifiedStudioProjectDirectoryInvalidError: When the project directory
            location in the metadata file is invalid.
        ProjectStorageMetadataJsonDecodeError: When reading from the JSON metadata file
            containing the project directory fails.

    """
    if is_md_environment:
        smus_project_dir_name = get_smus_project_dir_name()

        if smus_project_dir_name == "src":
            return validate_and_get_download_directory(
                home_path=HOME_PATH,
                target_download_dir=MD_PATH,
                target_download_dir_full_path=MD_NOTEBOOK_PATH,
            )
        return validate_and_get_download_directory(
            home_path=HOME_PATH,
            target_download_dir=MD_UNIFIED_STORAGE_PATH,
            target_download_dir_full_path=MD_UNIFIED_STORAGE_NOTEBOOK_PATH,
        )
    else:
        return NOTEBOOK_PATH
