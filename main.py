#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK

import argparse
import subprocess
import uiautomator2 as u2
import inquirer
from enum import Enum


def adb(command_args):
    return subprocess.run("adb -s " + device_id + " " + command_args, stdout=subprocess.PIPE, shell=True, universal_newlines=True)


def select_device():
    out = subprocess.run("adb devices", stdout=subprocess.PIPE, shell=True, universal_newlines=True)
    devices = out.stdout.split("\n")[1:]

    if len(devices) == 1:
        return devices[0].split("\t")[0]

    device_selection = [
        inquirer.List('device',
                      message="What device would you like to use?",
                      choices=devices,
                      ),
    ]
    answer = inquirer.prompt(device_selection)
    device = answer['device'].split("\t")[0]
    return device


class Scripts(Enum):
    clear_mail_db = "rmdb"
    show_layout_bounds = "bounds"
    login = "login"

    def __str__(self):
        return self.value


if __name__ == '__main__':
    device_id = select_device()

    parser = argparse.ArgumentParser()  # (description="Arguments for kmail")
    parser.add_argument('script', type=Scripts, choices=list(Scripts), help="what command to run")

    args = parser.parse_args()

    match args.script:
        case Scripts.clear_mail_db:
            adb("exec-out run-as com.infomaniak.mail find ./files -name 'Mailbox-*.realm' -exec rm {} \\;")

        case Scripts.show_layout_bounds:
            result = adb("shell getprop debug.layout")
            new_layout_state = "true" if (result.stdout.strip() == "false") else "false"
            print("Setting show layout bounds to " + new_layout_state)
            adb("shell setprop debug.layout " + new_layout_state)
            adb("shell service call activity 1599295570")

        case Scripts.login:
            d = u2.connect()
            out = d.dump_hierarchy()
            print(out)

        case other:
            print("Command not handled")
