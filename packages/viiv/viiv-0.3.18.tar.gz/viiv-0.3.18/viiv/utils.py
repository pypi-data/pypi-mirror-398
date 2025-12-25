#!/usr/bin/env python

import json
import os
from pathlib import Path
try:
    from importlib import resources
except ImportError:
    # Python < 3.9
    import importlib_resources as resources

from PIL import Image

PROJECT_NAME = "viiv"
THEME_SUFFIX = "-color-theme.json"
THEME_SNAPSHOT_SUFFIX = "-snapshot.jpg"

def write_json_file(json_file_path, content):
    """
    write the content to the json file
    """
    with open(json_file_path, 'w', encoding='utf-8') as f:
        json.dump(content, f, ensure_ascii=False, indent=4)

def save_image(img, output_dir, name):
    """
    Saves the image to a specified directory with a given name.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    img.save(os.path.join(output_dir, f"{name}{THEME_SNAPSHOT_SUFFIX}"))


def load_json_file(json_file_path):
    """
    Loads the JSON file at the specified path.
    """
    with open(json_file_path, "r", encoding="utf-8") as file:
        json_data = json.load(file)
        return json_data


def dump_json_file(json_file_path, json_data, indent=2):
    """
    Writes the given JSON data to a file at the specified path.
    """
    with open(json_file_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=indent)


def load_theme_data(theme_name):
    """Load theme data from the theme json file."""
    assert not theme_name.endswith(
        THEME_SUFFIX
    ), f"Invalid theme name: {theme_name}. It should not end with {THEME_SUFFIX}. Valid theme name example: viiv-dark."
    theme_name = theme_name.lower()
    root_path = os.getcwd() + os.sep
    theme_path = root_path + "themes" + os.sep + theme_name + THEME_SUFFIX
    theme_data = load_json_file(theme_path)
    return theme_data


def load_theme_snapshot(theme_name):
    """Load theme snapshot Image from the theme snapshot jpg file.

    Returns:
        Image: The theme snapshot Image
    """
    root_path = os.getcwd() + os.sep
    theme_snapshot_path = (
        root_path + "images" + os.sep + theme_name + THEME_SNAPSHOT_SUFFIX
    )
    theme_snapshot = Image.open(theme_snapshot_path)
    return theme_snapshot


def save_theme_snapshot(theme_name, theme_snapshot: Image):
    """Save theme snapshot Image to the theme snapshot jpg file.

    Args:
        theme_name (str): The theme name.
        theme_snapshot (Image): The theme snapshot Image.
    """
    root_path = os.getcwd() + os.sep
    theme_snapshot_path = (
        root_path + "images" + os.sep + theme_name + THEME_SNAPSHOT_SUFFIX
    )
    theme_snapshot.save(theme_snapshot_path)
    return theme_snapshot_path

def get_project_root_path():
    """Return the root path of the project - rdi-datastream-python-api."""
    file_abspath = os.path.abspath(__file__)
    project_root_path = file_abspath
    while not (project_root_path.endswith(PROJECT_NAME) and os.path.exists(Path(project_root_path) / ".git")):
        project_root_path = os.path.dirname(project_root_path)
        # in case the project name is changed without reflected by the constant
        # variable PROJECT_NAME
        assert (
            len(project_root_path) > len(PROJECT_NAME)
        ), f"The project name is not {PROJECT_NAME}\
 anymore. Please check and fix."

    return project_root_path


def load_package_json():
    """Load package.json file."""
    project_root_path = get_project_root_path()
    package_file_path = project_root_path + os.sep + "package.json"
    package_data = load_json_file(package_file_path)
    return package_data


def load_config_json():
    """Load config.json from package resources."""
    try:
        # Load from package resources (when installed)
        with resources.files('viiv').joinpath('conf/config.json').open('r', encoding='utf-8') as f:
            return json.load(f)
    except (ImportError, FileNotFoundError):
        # Fallback to packaged version during development
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_file_path = os.path.join(current_dir, 'conf', 'config.json')
        return load_json_file(config_file_path)