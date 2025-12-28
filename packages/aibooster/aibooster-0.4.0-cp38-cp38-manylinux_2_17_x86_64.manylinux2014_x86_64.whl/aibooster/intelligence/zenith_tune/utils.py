import os
import shutil
from typing import Any, Dict

from .distributed import get_rank


def staging_directory(command: str, old_path: str, new_path: str) -> str:
    """
    Replace directory paths in command and copy directory for distributed training.

    Only rank 0 performs the copy operation.

    Args:
        command: The shell command string
        old_path: Path to replace
        new_path: New path to use

    Returns:
        Modified command string

    Raises:
        FileNotFoundError: If old_path doesn't exist
        OSError: If copying fails
    """
    if not os.path.exists(old_path):
        raise FileNotFoundError(f"Source path does not exist: {old_path}")

    if not os.path.isdir(old_path):
        raise NotADirectoryError(f"Source path is not a directory: {old_path}")

    # Replace paths in command string directly
    modified_command = command.replace(old_path, new_path)

    if get_rank() == 0:
        try:
            shutil.copytree(old_path, new_path, dirs_exist_ok=True)
        except OSError as e:
            raise OSError(
                f"Failed to copy directory from {old_path} to {new_path}: {e}"
            )

    return modified_command


def replace_params_to_file(
    input_filepath: str,
    output_filepath: str,
    params: Dict[str, Any],
) -> None:
    """
    Replace parameters in a file with given values.

    Args:
        input_filepath (str): Path to the input file.
        output_filepath (str): Path to the output file.
        params (Dict[str, Any]): Dictionary of parameters to replace.
    """
    with open(input_filepath, "r") as f:
        content = f.read()
    for param_name, value in params.items():
        content = content.replace(f"{{{{{param_name}}}}}", f"{value}")
    with open(output_filepath, "w") as f:
        f.write(content)
