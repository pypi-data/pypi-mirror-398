class S3ObjectNotFoundError(Exception):
    """Exception throw if object doesn't not exist"""

    pass


class NotebookTooLargeError(Exception):
    """Exception throw if notebook size larger than NOTEBOOK_SIZE_LIMIT_IN_BYTES"""

    pass


class DownloadDirectoryNotFoundError(Exception):
    """Exception throw if download directory is not found"""

    pass


class SageMakerUnifiedStudioProjectDirectoryNotSetError(Exception):
    """Exception thrown if SMUS project directory env var not set in post startup script"""

    pass


class SageMakerUnifiedStudioProjectDirectoryInvalidError(Exception):
    """Exception thrown if it doesn't contain a valid project directory path"""

    pass


class SageMakerUnifiedStudioStorageMetadataFileNotFoundError(Exception):
    """Exception thrown if $HOME/.config/smus-storage-metadata.json not found"""

    pass


class ProjectStorageMetadataJsonDecodeError(Exception):
    """Exception thrown if error reading /opt/ml/metadata/resource-metadata.json"""

    pass
