#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK

import argparse
import subprocess

import inquirer
import eml_writer as ew


def adb(command_args):
    return subprocess.run("adb -s " + device_id + " " + command_args,
                          stdout=subprocess.PIPE,
                          shell=True,
                          universal_newlines=True)


def select_device():
    out = subprocess.run("adb devices", stdout=subprocess.PIPE, shell=True, universal_newlines=True)
    devices = out.stdout.split("\n")[1:]

    while "" in devices:
        devices.remove("")

    if len(devices) == 1:
        return devices[0].split("\t")[0]

    device_selection = [inquirer.List('device', message="What device would you like to use?", choices=devices)]
    answer = inquirer.prompt(device_selection)
    device = answer['device'].split("\t")[0]
    return device


def clear_mail_db(args):
    global device_id
    device_id = select_device()

    adb("exec-out run-as com.infomaniak.mail find ./files -name 'Mailbox-*-*.realm*' -exec rm {} \\;")
    adb("exec-out run-as com.infomaniak.mail find ./cache -name '*_cache' -exec rm -r {} \\;")
    adb("exec-out run-as com.infomaniak.mail find ./files -name 'network-response-body-*' -exec rm {} \\;")


def show_layout_bounds(args):
    global device_id
    device_id = select_device()

    result = adb("shell getprop debug.layout")
    new_layout_state = "true" if (result.stdout.strip() == "false") else "false"
    print("Setting show layout bounds to " + new_layout_state)
    adb("shell setprop debug.layout " + new_layout_state)
    adb("shell service call activity 1599295570")


def generate_eml(args):
    ew.new_eml(args.subject, args.sender, args.to, args.cc, args.bcc, args.html)


if __name__ == '__main__':
    device_id = None

    parser = argparse.ArgumentParser()  # (description="Arguments for kmail")
    subparsers = parser.add_subparsers(dest='cmd', help='sub-command help')

    clear_mail_db_parser = subparsers.add_parser("rmdb")
    clear_mail_db_parser.set_defaults(func=show_layout_bounds)

    bounds_parser = subparsers.add_parser("bounds")
    bounds_parser.set_defaults(func=show_layout_bounds)

    eml_parser = subparsers.add_parser("eml")
    eml_parser.add_argument("html")
    eml_parser.add_argument("-s", "--subject", dest="subject")
    eml_parser.add_argument("-f", "--from", dest="sender")
    eml_parser.add_argument("-t", "--to", dest="to")
    eml_parser.add_argument("-c", "--cc", dest="cc")
    eml_parser.add_argument("-b", "--bcc", dest="bcc")
    eml_parser.set_defaults(func=generate_eml)

    args = parser.parse_args()
    args.func(args)
