#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK

import argparse
import pathlib
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
    ew.new_eml(args.subject, args.sender, args.to, args.cc, args.html)


def copy_last_video(args):
    global device_id
    device_id = select_device()

    root = pathlib.Path.home().__str__() + "/"
    desktop = "Desktop/"
    destination = root + desktop
    if args.here:
        destination = "./"

    movie_dir = "storage/emulated/0/Movies/"
    filename = adb("shell ls -tp " + movie_dir + " | grep -v /$ | head -1").stdout.strip()
    file = movie_dir + filename
    adb("pull " + file + " " + destination)
    print("Pulled " + filename + " successfully")

    if args.open:
        subprocess.Popen(("open", destination + filename), cwd=None)


if __name__ == '__main__':
    device_id = None

    parser = argparse.ArgumentParser()  # (description="Arguments for kmail")
    subparsers = parser.add_subparsers(dest='cmd', help='sub-command help')

    clear_mail_db_parser = subparsers.add_parser("rmdb", help="deletes all of the databases containg mails or "
                                                              "attachment cache but keeps the account logged in using"
                                                              " adb")
    clear_mail_db_parser.set_defaults(func=clear_mail_db)

    bounds_parser = subparsers.add_parser("bounds", help="toggles layout bounds for the android device using adb")
    bounds_parser.set_defaults(func=show_layout_bounds)

    eml_parser = subparsers.add_parser("eml", help="creates an eml file in the current directory")
    eml_parser.add_argument("html", nargs="?", help="html code of the content of the mail", )
    eml_parser.add_argument("-s", "--subject", dest="subject", help="subject of the mail")
    eml_parser.add_argument("-f", "--from", dest="sender", help="sender of the mail. Comma separated if there's more "
                                                                "than one. To have a recipient with a name and an "
                                                                "email follow this pattern: name <email@domain.ext>")
    eml_parser.add_argument("-t", "--to", dest="to", help="recipient of the mail. Comma separated if there's more "
                                                          "than one")
    eml_parser.add_argument("-c", "--cc", dest="cc", help="recipient of a copy of the mail. Comma separated if "
                                                          "there's mor than one")
    eml_parser.set_defaults(func=generate_eml)

    last_video_parser = subparsers.add_parser("lastvid",
                                              help="copies last recorded video of the emulator to the desktop")
    last_video_parser.add_argument("-o", "--open", action="store_true", default=False,
                                   help="opens the file in default player at the same time")
    last_video_parser.add_argument("--here", action="store_true", default=False,
                                   help="downloads the file in current directory instead of desktop")
    last_video_parser.set_defaults(func=copy_last_video)

    args = parser.parse_args()
    args.func(args)
