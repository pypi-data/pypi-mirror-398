import codecs
import json
import os
from typing import Dict, List, Text, Union


def load_json(file_path: Text) -> Union[Dict, List]:
    """
    Load content from json file

    Args:
        file_path (Text): json path

    Returns: a dictionary

    """
    with codecs.open(file_path, "r", "utf-8-sig") as f:
        config = json.load(f)

    return config


def get_extension(filename):
    return os.path.splitext(filename)[1]


def get_all_files_in_directory(directory, extensions=None):
    """
    Returns a list of all files in a directory, optionally filtered by file
    Args:
        directory: the directory to search
        extensions: List of extensions to filter by. If None, return all files
            Examples: [".md", ".txt"]

    Returns:

    """

    extensions = extensions or []
    extensions = [extensions] if isinstance(extensions, str) else extensions
    new_extensions = []
    for ext in extensions:
        ext = f".{ext}" if not ext.startswith(".") else ext
        new_extensions.append(ext)

    files = [
        os.path.join(dirpath, file)
        for dirpath, dirnames, files in os.walk(directory)
        for file in files
    ]
    filtered_files = []
    for file in files:
        if new_extensions and get_extension(file) in new_extensions:
            filtered_files.append(file)
        elif not new_extensions:
            filtered_files.append(file)
    return filtered_files
