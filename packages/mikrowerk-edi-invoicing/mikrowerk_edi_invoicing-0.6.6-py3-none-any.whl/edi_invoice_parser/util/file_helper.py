"""
Helper functions for working with files and directories.
"""

from os import path as os_path


def get_checked_file_path(file_path: str, rel_file=None) -> (str, bool, bool):
    """
    get relative or absolute file path
    Args:
        file_path: path to file, relative or absolute
        rel_file: if not none then this is the base dir-path to the file_path

    Returns: (str, bool, bool) resulting path to file, file exists, is directory

    """
    if rel_file is None or file_path.startswith("/"):
        _path = os_path.normpath(file_path)  # absolute
    else:
        rel_dir = os_path.dirname(rel_file)
        fp = os_path.normpath(file_path)
        _path = os_path.join(rel_dir, fp)
    return _path, os_path.exists(_path), os_path.isdir(_path)
