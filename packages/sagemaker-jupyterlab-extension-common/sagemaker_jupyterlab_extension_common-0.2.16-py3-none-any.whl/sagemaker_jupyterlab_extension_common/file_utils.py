import os


def save_to_ebs(
    base_file_path: str, file_name: str, content: str, ext: str = "ipynb"
) -> str:
    """Save the content to the target path, return the absolute path."""
    directory_path = os.path.dirname(base_file_path)

    os.makedirs(directory_path, exist_ok=True)

    absolute_file_path = _get_unique_path(directory_path, file_name, ext)

    with open(absolute_file_path, "w") as f:
        f.write(content)

    return absolute_file_path


def _get_unique_path(directory_path: str, file_name: str, ext: str) -> str:
    """
    Returns a unique file name based on the given file name and file extension.
    """
    absolute_file_path = os.path.join(directory_path, f"{file_name}.{ext}")

    suffix = 0
    while os.path.exists(absolute_file_path):
        suffix += 1
        absolute_file_path = os.path.join(directory_path, f"{file_name}_{suffix}.{ext}")
    return absolute_file_path
