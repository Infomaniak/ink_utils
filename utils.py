import inquirer


def remove_empty_items(array):
    return [value for value in array if value != ""]


def select_in_list(message, choices):
    if len(choices) == 1:
        return choices[0]
    return inquirer.prompt([inquirer.List('choice', message=message, choices=choices)])['choice']


def accept_substitution(input):
    if input is not None and input.startswith("/dev/fd"):
        with open(input, "r") as fd:
            output = fd.read().strip()
    else:
        output = input

    return output
