import json
from pathlib import Path
from unittest.mock import MagicMock, Mock, call, mock_open, patch

import pytest
from sagemaker_jupyterlab_extension_common.exceptions import (
    DownloadDirectoryNotFoundError,
    ProjectStorageMetadataJsonDecodeError,
    SageMakerUnifiedStudioProjectDirectoryInvalidError,
    SageMakerUnifiedStudioProjectDirectoryNotSetError,
    SageMakerUnifiedStudioStorageMetadataFileNotFoundError,
)
from sagemaker_jupyterlab_extension_common.jumpstart.notebook_utils import (
    get_jumpstart_notebook_name,
    get_jumpstart_notebook_suffix,
    get_smus_project_dir_name,
    generate_notebook_download_path,
    is_project_dir_name_key_present,
    is_valid_notebook_resource_type,
    notebook_transformation_needed,
    read_project_dir_name_from_json_file,
    validate_and_get_download_directory,
)
from sagemaker_jupyterlab_extension_common.jumpstart.notebook_types import (
    JumpStartResourceType,
)


@pytest.mark.parametrize(
    "model_id,key,resource_type,expected",
    [
        (
            "mock_model_id",
            "mock/key.ipynb",
            JumpStartResourceType.inferNotebook,
            "mock_model_id_infer",
        ),
        (
            None,
            "mock/key.ipynb",
            JumpStartResourceType.inferNotebook,
            "key_infer",
        ),
    ],
)
def test_get_jumpstart_notebook_name(model_id, key, resource_type, expected):
    assert get_jumpstart_notebook_name(model_id, key, resource_type) == expected


@pytest.mark.parametrize(
    "resource_type,expected",
    [
        (JumpStartResourceType.inferNotebook, "infer"),
        (JumpStartResourceType.modelSdkNotebook, "sdk"),
        (JumpStartResourceType.proprietaryNotebook, "pp"),
    ],
)
def test_get_jumpstart_notebook_suffix(resource_type, expected):
    assert expected == get_jumpstart_notebook_suffix(resource_type)


@pytest.mark.parametrize(
    "resource_type,expected",
    [
        (JumpStartResourceType.inferNotebook, True),
        (JumpStartResourceType.modelSdkNotebook, True),
        (JumpStartResourceType.proprietaryNotebook, False),
    ],
)
def test_notebook_transformation_needed(resource_type, expected):
    assert expected == notebook_transformation_needed(resource_type)


@pytest.mark.parametrize(
    "resource_type,expected",
    [
        ("inferNotebook", True),
        ("modelSdkNotebook", True),
        ("proprietaryNotebook", True),
        ("otherNotebook", False),
    ],
)
def test_is_valid_notebook_resource_type(resource_type, expected):
    assert expected == is_valid_notebook_resource_type(resource_type)


class TestIsProjectDirNameKeyPresent:
    """Tests for the is_project_dir_name_key_present function"""

    @pytest.mark.parametrize(
        "json_content,validate_function,expected_result",
        [
            # Key exists in the JSON
            (
                {"AdditionalMetadata": {"ProjectSharedDirectory": "/path/to/src"}},
                lambda json_obj: "ProjectSharedDirectory"
                in json_obj.get("AdditionalMetadata", {}),
                True,
            ),
            # Key doesn't exist in the JSON
            (
                {"AdditionalMetadata": {}},
                lambda json_obj: "ProjectSharedDirectory"
                in json_obj.get("AdditionalMetadata", {}),
                False,
            ),
            # Different structure, key exists
            (
                {"smusProjectDirectory": "/path/to/shared"},
                lambda json_obj: "smusProjectDirectory" in json_obj,
                True,
            ),
            # Different structure, key doesn't exist
            (
                {},
                lambda json_obj: "smusProjectDirectory" in json_obj,
                False,
            ),
        ],
    )
    def test_successful_key_validation(
        self, json_content, validate_function, expected_result
    ):
        """Test successful validation of key presence"""
        with patch("pathlib.Path.open", mock_open(read_data=json.dumps(json_content))):
            result = is_project_dir_name_key_present(
                file_path="test_path.json",
                validate_key_exists=validate_function,
            )
            assert result == expected_result

    def test_json_decode_error(self):
        """Test handling of JSON decode errors"""
        with patch("pathlib.Path.open", mock_open(read_data="{invalid:json}")):
            with pytest.raises(ProjectStorageMetadataJsonDecodeError):
                is_project_dir_name_key_present(
                    file_path="test_path.json",
                    validate_key_exists=lambda x: True,
                )


class TestReadProjectDirNameFromJsonFile:
    """Tests for the read_project_dir_name_from_json_file function"""

    @pytest.mark.parametrize(
        "json_content,get_enclosing_object,key,expected",
        [
            # Resource metadata JSON with src
            (
                {"AdditionalMetadata": {"ProjectSharedDirectory": "/path/to/src"}},
                lambda json_obj: json_obj.get("AdditionalMetadata", {}),
                "ProjectSharedDirectory",
                "src",
            ),
            # Resource metadata JSON with shared
            (
                {"AdditionalMetadata": {"ProjectSharedDirectory": "/path/to/shared"}},
                lambda json_obj: json_obj.get("AdditionalMetadata", {}),
                "ProjectSharedDirectory",
                "shared",
            ),
            # SMUS project directory JSON with src
            (
                {"smusProjectDirectory": "/path/to/src"},
                lambda json_obj: json_obj,
                "smusProjectDirectory",
                "src",
            ),
            # SMUS project directory JSON with shared
            (
                {"smusProjectDirectory": "/path/to/shared"},
                lambda json_obj: json_obj,
                "smusProjectDirectory",
                "shared",
            ),
        ],
    )
    def test_successful_reads(self, json_content, get_enclosing_object, key, expected):
        """Test successful reading of project directory name from various JSON structures"""
        with patch("pathlib.Path.open", mock_open(read_data=json.dumps(json_content))):
            result = read_project_dir_name_from_json_file(
                file_path="test_path.json",
                get_project_dir_name_enclosing_object=get_enclosing_object,
                project_dir_name_key=key,
            )
            assert result == expected

    def test_json_decode_error(self):
        """Test handling of JSON decode errors"""
        with patch("pathlib.Path.open", mock_open(read_data="{invalid:json}")):
            with pytest.raises(ProjectStorageMetadataJsonDecodeError):
                read_project_dir_name_from_json_file(
                    file_path="test_path.json",
                    get_project_dir_name_enclosing_object=lambda x: x,
                    project_dir_name_key="any_key",
                )

    @pytest.mark.parametrize(
        "json_content,get_enclosing_object,key",
        [
            # Missing key in resource metadata
            (
                {"AdditionalMetadata": {}},
                lambda json_obj: json_obj.get("AdditionalMetadata", {}),
                "ProjectSharedDirectory",
            ),
            # Empty value in resource metadata
            (
                {"AdditionalMetadata": {"ProjectSharedDirectory": ""}},
                lambda json_obj: json_obj.get("AdditionalMetadata", {}),
                "ProjectSharedDirectory",
            ),
            # Missing key in SMUS project directory
            (
                {},
                lambda json_obj: json_obj,
                "smusProjectDirectory",
            ),
            # Empty value in SMUS project directory
            (
                {"smusProjectDirectory": ""},
                lambda json_obj: json_obj,
                "smusProjectDirectory",
            ),
        ],
    )
    def test_directory_not_set(self, json_content, get_enclosing_object, key):
        """Test error when project directory is not set in the JSON"""
        with patch("pathlib.Path.open", mock_open(read_data=json.dumps(json_content))):
            with pytest.raises(SageMakerUnifiedStudioProjectDirectoryNotSetError):
                read_project_dir_name_from_json_file(
                    file_path="test_path.json",
                    get_project_dir_name_enclosing_object=get_enclosing_object,
                    project_dir_name_key=key,
                )

    @pytest.mark.parametrize(
        "json_content,get_enclosing_object,key",
        [
            # Invalid directory in resource metadata
            (
                {"AdditionalMetadata": {"ProjectSharedDirectory": "/path/to/invalid"}},
                lambda json_obj: json_obj.get("AdditionalMetadata", {}),
                "ProjectSharedDirectory",
            ),
            # Invalid directory in SMUS project directory
            (
                {"smusProjectDirectory": "/path/to/invalid"},
                lambda json_obj: json_obj,
                "smusProjectDirectory",
            ),
        ],
    )
    def test_invalid_directory(self, json_content, get_enclosing_object, key):
        """Test error when project directory path is invalid"""
        with patch("pathlib.Path.open", mock_open(read_data=json.dumps(json_content))):
            with pytest.raises(SageMakerUnifiedStudioProjectDirectoryInvalidError):
                read_project_dir_name_from_json_file(
                    file_path="test_path.json",
                    get_project_dir_name_enclosing_object=get_enclosing_object,
                    project_dir_name_key=key,
                )


class AnyCallable:
    def __eq__(self, other):
        return callable(other)


class TestGetSmusProjectDirName:
    """Tests for the get_smus_project_dir_name function"""

    RESOURCE_METADATA_PATH = "/opt/ml/metadata/resource-metadata.json"
    SMUS_PROJECT_DIR_PATH = str(Path.home() / ".config/smus-storage-metadata.json")

    @patch(
        "sagemaker_jupyterlab_extension_common.jumpstart.notebook_utils.is_project_dir_name_key_present"
    )
    @patch(
        "sagemaker_jupyterlab_extension_common.jumpstart.notebook_utils.read_project_dir_name_from_json_file"
    )
    def test_resource_metadata_exists_with_key(self, mock_read, mock_key_present):
        """Test when resource metadata file exists and key is present"""
        # Setup mocks
        mock_key_present.return_value = True
        mock_read.return_value = "src"

        def fake_exists(p: Path) -> bool:
            return str(p) == self.RESOURCE_METADATA_PATH

        with patch.object(Path, "exists", fake_exists):
            # Call function
            result = get_smus_project_dir_name()

            # Check results
            assert result == "src"
            mock_key_present.assert_called_once()
            mock_read.assert_called_once_with(
                file_path=self.RESOURCE_METADATA_PATH,
                get_project_dir_name_enclosing_object=AnyCallable(),
                project_dir_name_key="ProjectSharedDirectory",
            )

    @patch(
        "sagemaker_jupyterlab_extension_common.jumpstart.notebook_utils.is_project_dir_name_key_present"
    )
    @patch(
        "sagemaker_jupyterlab_extension_common.jumpstart.notebook_utils.read_project_dir_name_from_json_file"
    )
    def test_resource_metadata_exists_without_key(self, mock_read, mock_key_present):
        """Test when resource metadata file exists but key is missing, fallback to SMUS"""
        # Setup mocks
        mock_key_present.return_value = False
        mock_read.return_value = "shared"

        def fake_exists(path: Path) -> bool:
            return str(path) in [
                self.RESOURCE_METADATA_PATH,
                self.SMUS_PROJECT_DIR_PATH,
            ]

        with patch.object(Path, "exists", fake_exists):
            # Call function
            result = get_smus_project_dir_name()

            # Check results
            assert result == "shared"

            mock_key_present.assert_called_once()
            mock_read.assert_called_once_with(
                file_path=self.SMUS_PROJECT_DIR_PATH,
                get_project_dir_name_enclosing_object=AnyCallable(),
                project_dir_name_key="smusProjectDirectory",
            )

    @patch(
        "sagemaker_jupyterlab_extension_common.jumpstart.notebook_utils.read_project_dir_name_from_json_file"
    )
    def test_smus_project_dir_exists(self, mock_read):
        """Test when SMUS project directory file exists but resource metadata doesn't"""
        # Setup mocks
        mock_read.return_value = "shared"

        def fake_exists(path):
            if str(path) == self.RESOURCE_METADATA_PATH:
                return False
            if str(path) == self.SMUS_PROJECT_DIR_PATH:
                return True
            return False

        with patch.object(Path, "exists", fake_exists):
            # Call function
            result = get_smus_project_dir_name()

            # Check results
            assert result == "shared"
            mock_read.assert_called_once_with(
                file_path=self.SMUS_PROJECT_DIR_PATH,
                get_project_dir_name_enclosing_object=AnyCallable(),
                project_dir_name_key="smusProjectDirectory",
            )

    def test_neither_file_exists(self):
        """Test when neither file exists"""
        with patch.object(Path, "exists", autospec=True) as mock_exists:
            # Configure Path.exists to return False for both paths
            mock_exists.return_value = False

            # Call function and check exception
            with pytest.raises(SageMakerUnifiedStudioStorageMetadataFileNotFoundError):
                get_smus_project_dir_name()

            # Check that both files were checked
            mock_exists.assert_has_calls(
                [
                    call(Path(self.RESOURCE_METADATA_PATH)),
                    call(Path(self.SMUS_PROJECT_DIR_PATH)),
                ]
            )


class TestValidateAndGetDownloadDirectory:
    """Tests for the validate_and_get_download_directory function"""

    @patch("pathlib.Path.joinpath")
    def test_directory_exists(self, mock_joinpath):
        """Test when target directory exists"""
        # Setup mocks
        mock_path = MagicMock()
        mock_path.is_dir.return_value = True
        mock_joinpath.return_value = mock_path

        # Test parameters
        home_path = "/home/user"
        target_dir = "target_dir"
        full_path = "/home/user/target_dir/DemoNotebooks"

        # Call function
        result = validate_and_get_download_directory(home_path, target_dir, full_path)

        # Check results
        assert result == full_path
        mock_joinpath.assert_called_once_with(target_dir)
        mock_path.is_dir.assert_called_once()

    @patch("pathlib.Path.joinpath")
    def test_directory_not_found(self, mock_joinpath):
        """Test when target directory doesn't exist"""
        # Setup mocks
        mock_path = MagicMock()
        mock_path.is_dir.return_value = False
        mock_joinpath.return_value = mock_path

        # Test parameters
        home_path = "/home/user"
        target_dir = "missing_dir"
        full_path = "/home/user/missing_dir/DemoNotebooks"

        # Call function and check exception
        with pytest.raises(DownloadDirectoryNotFoundError):
            validate_and_get_download_directory(home_path, target_dir, full_path)

        # Check that the directory was checked
        mock_joinpath.assert_called_once_with(target_dir)
        mock_path.is_dir.assert_called_once()


class TestGenerateNotebookDownloadPath:
    """Tests for the generate_notebook_download_path function"""

    @patch(
        "sagemaker_jupyterlab_extension_common.jumpstart.notebook_utils.get_smus_project_dir_name"
    )
    @patch(
        "sagemaker_jupyterlab_extension_common.jumpstart.notebook_utils.validate_and_get_download_directory"
    )
    def test_md_environment_src(self, mock_validate, mock_get_dir_name):
        """Test with MD environment and src project directory"""
        from sagemaker_jupyterlab_extension_common.jumpstart.constants import (
            HOME_PATH,
            MD_PATH,
            MD_NOTEBOOK_PATH,
        )

        # Setup mocks
        mock_get_dir_name.return_value = "src"
        mock_validate.return_value = MD_NOTEBOOK_PATH

        # Call function
        result = generate_notebook_download_path(is_md_environment=True)

        # Check results
        assert result == MD_NOTEBOOK_PATH
        mock_get_dir_name.assert_called_once()
        mock_validate.assert_called_once_with(
            home_path=HOME_PATH,
            target_download_dir=MD_PATH,
            target_download_dir_full_path=MD_NOTEBOOK_PATH,
        )

    @patch(
        "sagemaker_jupyterlab_extension_common.jumpstart.notebook_utils.get_smus_project_dir_name"
    )
    @patch(
        "sagemaker_jupyterlab_extension_common.jumpstart.notebook_utils.validate_and_get_download_directory"
    )
    def test_md_environment_shared(self, mock_validate, mock_get_dir_name):
        """Test with MD environment and shared project directory"""
        from sagemaker_jupyterlab_extension_common.jumpstart.constants import (
            HOME_PATH,
            MD_UNIFIED_STORAGE_PATH,
            MD_UNIFIED_STORAGE_NOTEBOOK_PATH,
        )

        # Setup mocks
        mock_get_dir_name.return_value = "shared"
        mock_validate.return_value = MD_UNIFIED_STORAGE_NOTEBOOK_PATH

        # Call function
        result = generate_notebook_download_path(is_md_environment=True)

        # Check results
        assert result == MD_UNIFIED_STORAGE_NOTEBOOK_PATH
        mock_get_dir_name.assert_called_once()
        mock_validate.assert_called_once_with(
            home_path=HOME_PATH,
            target_download_dir=MD_UNIFIED_STORAGE_PATH,
            target_download_dir_full_path=MD_UNIFIED_STORAGE_NOTEBOOK_PATH,
        )

    def test_non_md_environment(self):
        """Test with non-MD environment"""
        from sagemaker_jupyterlab_extension_common.jumpstart.constants import (
            NOTEBOOK_PATH,
        )

        # Call function
        result = generate_notebook_download_path(is_md_environment=False)

        # Check results - should just return NOTEBOOK_PATH without any checks
        assert result == NOTEBOOK_PATH

    @patch(
        "sagemaker_jupyterlab_extension_common.jumpstart.notebook_utils.get_smus_project_dir_name"
    )
    @patch(
        "sagemaker_jupyterlab_extension_common.jumpstart.notebook_utils.validate_and_get_download_directory"
    )
    def test_directory_not_found_propagates_error(
        self, mock_validate, mock_get_dir_name
    ):
        """Test that DownloadDirectoryNotFoundError from validate_and_get_download_directory is propagated"""
        # Setup mocks
        mock_get_dir_name.return_value = "src"
        mock_validate.side_effect = DownloadDirectoryNotFoundError(
            "Directory not found"
        )

        # Call function and check exception
        with pytest.raises(DownloadDirectoryNotFoundError):
            generate_notebook_download_path(is_md_environment=True)
