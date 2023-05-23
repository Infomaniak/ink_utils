import os
import configparser

script_folder = os.path.dirname(__file__)
config_filename = "settings.txt"
config_file = script_folder + '/' + config_filename
missing_config_file = True

if os.path.exists(config_file):
    missing_config_file = False

    config_parser = configparser.ConfigParser()
    config_parser.read_file(open(config_file))


def get(section, key):
    if missing_config_file:
        print(f"Missing {config_filename} file at {script_folder}")
        quit()

    return config_parser.get(section, key)
