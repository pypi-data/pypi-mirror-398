"""Naming conventions for generated code.

Converts dataset IDs to valid Python module names and filenames.
"""

from __future__ import annotations

import re


def dataset_id_to_filename(dataset_id: str) -> str:
    """Convert dataset ID to a filename.

    Args:
        dataset_id: Dataset ID in workspace/name format

    Returns:
        Filename like workspace_name_loader.py

    Examples:
        >>> dataset_id_to_filename("vision/coco")
        'vision_coco_loader.py'
        >>> dataset_id_to_filename("my-org/my-dataset")
        'my_org_my_dataset_loader.py'
    """
    # Replace / and - with _
    name = dataset_id.replace("/", "_").replace("-", "_")
    # Remove any non-alphanumeric characters except _
    name = re.sub(r"[^a-zA-Z0-9_]", "", name)
    # Ensure it doesn't start with a number
    if name and name[0].isdigit():
        name = "_" + name
    return f"{name}_loader.py"


def dataset_id_to_module_name(dataset_id: str) -> str:
    """Convert dataset ID to a Python module name.

    Args:
        dataset_id: Dataset ID in workspace/name format

    Returns:
        Module name like vision_coco_loader

    Examples:
        >>> dataset_id_to_module_name("vision/coco")
        'vision_coco_loader'
    """
    filename = dataset_id_to_filename(dataset_id)
    return filename.replace(".py", "")


def column_to_function_name(column: str, prefix: str = "decode") -> str:
    """Convert a column name to a helper function name.

    Args:
        column: Column name
        prefix: Function prefix (default: decode)

    Returns:
        Function name like decode_images

    Examples:
        >>> column_to_function_name("image", "decode")
        'decode_image'
        >>> column_to_function_name("audio_path", "decode")
        'decode_audio_path'
    """
    # Clean up the column name
    name = re.sub(r"[^a-zA-Z0-9_]", "_", column)
    return f"{prefix}_{name}"
