import os

import yaml

script_folder = os.path.dirname(__file__)
config_filename = "settings.yml"
config_file = script_folder + '/' + config_filename
missing_config_file = True

project_key = "mail"

if os.path.exists(config_file):
    missing_config_file = False

    with open(config_file) as f:
        config = yaml.safe_load(f)


def get_project(section, key, raise_error=True):
    return _get(project_key, section, key, raise_error)


def get_global(section, key, raise_error=True):
    return _get("global", section, key, raise_error)


def _get(root_key, section, key, raise_error):
    if missing_config_file:
        print(f"Missing {config_filename} file at {script_folder}")
        quit()

    project = config[root_key]

    value = project[section][key]
    if raise_error and value is None:
        raise Exception(f"Missing ink setting in {config_filename}: {root_key} > {section} > {key}")

    return value
