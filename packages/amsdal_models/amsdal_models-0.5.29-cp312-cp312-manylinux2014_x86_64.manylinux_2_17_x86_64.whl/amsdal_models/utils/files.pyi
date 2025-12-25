from typing import Any

def convert_data_to_base64(file_data: Any) -> bytes:
    """
    Converts the given file data to a base64-encoded bytes object.

    This function takes any file data, converts it to bytes if it is a string, and then encodes it in base64 format.
    If the file data is already base64-encoded, it ensures the encoding is valid.

    Args:
        file_data (Any): The file data to be converted. It can be a string or bytes.

    Returns:
        bytes: The base64-encoded bytes object.
    """
