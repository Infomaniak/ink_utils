import importlib.util
import os
import random
import sys

import inquirer
from inquirer.themes import Default as DefaultTheme

ink_folder = os.path.abspath(os.path.dirname(__file__))

# Custom overridable theme
CUSTOM_CLASS_FILE = ink_folder + "/inquirer_theme.py"
CLASS_NAME = "InkTheme"
CurrentInkTheme = DefaultTheme

if os.path.isfile(CUSTOM_CLASS_FILE):
    spec = importlib.util.spec_from_file_location("inquirer_theme", CUSTOM_CLASS_FILE)
    custom_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(custom_module)

    # Check if the user defined the class
    if hasattr(custom_module, CLASS_NAME):
        CurrentInkTheme = getattr(custom_module, CLASS_NAME)
    else:
        pass
else:
    pass


def remove_empty_items(array):
    return [value for value in array if value != ""]


def select_in_list(message, choices):
    if len(choices) == 1:
        return choices[0]
    return inquirer.prompt([inquirer.List('choice', message=message, choices=choices)], theme=CurrentInkTheme())['choice']


def accept_substitution(input):
    if input is not None and input.startswith("/dev/fd"):
        with open(input, "r") as fd:
            output = fd.read().strip()
    else:
        output = input

    return output


def cancel_ink_command(message_end='\n'):
    if random.randint(0, 5) == 0:
        cancel_author = random.choice([
            "Marc",
            "a rogue AI gaining self-awareness",
            "a mysterious force",
            "Dave, who insists he knows best",
            "a cat walking on the keyboard",
            "a sentient paperclip offering help",
            "a time traveler who knows something we don’t",
            "a dramatic plot twist",
            "your neighbor colleague",
        ])
    else:
        cancel_author = "user"
    print(f'\nOperation cancelled by {cancel_author}', end=message_end)
    sys.exit(0)
