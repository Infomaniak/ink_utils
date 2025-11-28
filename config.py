import os
from pathlib import Path

import yaml

script_folder = os.path.dirname(__file__)
config_filename = "settings.yml"
current_project_filename = ".current_project"
config_file = script_folder + '/' + config_filename
current_project_file = script_folder + '/' + current_project_filename
missing_config_file = True

project_key = None


def list_projects():
    ensure_settings_exist()
    return [key for key in config.keys() if key != "global"]


def get_project(section, key, raise_error=True):
    return _get(project_key, section, key, raise_error)


def get_global(section, key, raise_error=True):
    return _get("global", section, key, raise_error)


def manually_get_project(root_key, section, key, raise_error=True):
    return _get(root_key, section, key, raise_error)


def get_project_module_parent():
    return Path(get_project("global", "project_root")) / ".."


def _get(root_key, section, key, raise_error):
    ensure_settings_exist()

    project = config[root_key]

    if raise_error and (section not in project or project[section] is None or key not in project[section]):
        print(f"Missing ink setting in {config_filename}: {root_key} > {section} > {key}")
        exit(1)

    value = None
    try:
        value = project[section][key]
    except:
        pass

    if raise_error and value is None:
        print(f"Missing ink setting in {config_filename}: {root_key} > {section} > {key}")
        exit(1)

    return value


def ensure_settings_exist():
    if missing_config_file:
        print(f"Missing {config_filename} file at {script_folder}")
        exit(1)


if os.path.exists(config_file):
    missing_config_file = False

    with open(config_file) as f:
        config = yaml.safe_load(f)

    if os.path.exists(current_project_file):
        with open(current_project_file) as f:
            project_key = f.readlines()[0].strip()
    else:
        project_key = list_projects()[0]
