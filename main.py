#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK

import argparse
import subprocess
import uiautomator2 as u2
import inquirer


def adb(command_args):
    return subprocess.run("adb -s " + device_id + " " + command_args,
                          stdout=subprocess.PIPE,
                          shell=True,
                          universal_newlines=True)


def select_device():
    out = subprocess.run("adb devices", stdout=subprocess.PIPE, shell=True, universal_newlines=True)
    devices = out.stdout.split("\n")[1:]

    if len(devices) == 1:
        return devices[0].split("\t")[0]

    device_selection = [inquirer.List('device', message="What device would you like to use?", choices=devices)]
    answer = inquirer.prompt(device_selection)
    device = answer['device'].split("\t")[0]
    return device


def clear_mail_db():
    global device_id
    device_id = select_device()

    adb("exec-out run-as com.infomaniak.mail find ./files -name 'Mailbox-*.realm' -exec rm {} \\;")


def show_layout_bounds():
    global device_id
    device_id = select_device()

    result = adb("shell getprop debug.layout")
    new_layout_state = "true" if (result.stdout.strip() == "false") else "false"
    print("Setting show layout bounds to " + new_layout_state)
    adb("shell setprop debug.layout " + new_layout_state)
    adb("shell service call activity 1599295570")


if __name__ == '__main__':
    device_id = None

    parser = argparse.ArgumentParser()  # (description="Arguments for kmail")
    subparsers = parser.add_subparsers(dest='cmd', help='sub-command help')

    clear_mail_db_parser = subparsers.add_parser("rmdb")

    bounds_parser = subparsers.add_parser("bounds")

    args = parser.parse_args()

    match args.cmd:
        case "rmdb":
            clear_mail_db()

        case "bounds":
            show_layout_bounds()

        case "login":
            d = u2.connect()
            out = d.dump_hierarchy()
            print(out)

        case other:
            print("Command not handled")
