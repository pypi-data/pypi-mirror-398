def get_file_format(file_path: str) -> str:
    """
    Get the format of a file.
    """
    return file_path.split(".")[-1]