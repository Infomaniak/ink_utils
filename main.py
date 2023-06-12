#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK

import argparse
import os
import pathlib
import shutil
import subprocess

from adb import adb, select_device, close_app, open_app
from utils import remove_empty_items, select_in_list
import eml_writer as ew
import loco_updater as lu
import login as lg


def clear_mail_db(args):
    device_id = select_device()

    adb("exec-out run-as com.infomaniak.mail find ./files -name 'Mailbox-*-*.realm*' -exec rm {} \\;", device_id)
    adb("exec-out run-as com.infomaniak.mail find ./cache -name '*_cache' -exec rm -r {} \\;", device_id)
    adb("exec-out run-as com.infomaniak.mail find ./files -name 'network-response-body-*' -exec rm {} \\;", device_id)

    if args.restart:
        close_app(device_id)
        open_app(device_id)


def show_layout_bounds(args):
    device_id = select_device()

    result = adb("shell getprop debug.layout", device_id)
    print("When getting current prop state we get: [" + result.stdout.strip() + "]")
    new_layout_state = "false" if (result.stdout.strip() == "true") else "true"
    print("Setting show layout bounds to " + new_layout_state)
    adb("shell setprop debug.layout " + new_layout_state, device_id)
    adb("shell service call activity 1599295570", device_id)


def generate_eml(args):
    ew.new_eml(args.subject, args.sender, args.to, args.cc, args.html)


def copy_last_video(args):
    device_id = select_device()

    root = pathlib.Path.home().__str__() + "/"
    desktop = "Desktop/"
    destination = root + desktop
    if args.here:
        destination = "./"

    movie_dir = "storage/emulated/0/Movies/"
    filename = adb("shell ls -tp " + movie_dir + " | grep -v /$ | head -1", device_id).stdout.strip()
    file = movie_dir + filename
    adb("pull " + file + " " + destination, device_id)
    print("Pulled " + filename + " successfully")

    if args.open:
        subprocess.Popen(("open", destination + filename), cwd=None)


def update_loco(args):
    lu.update_loco()


def login(args):
    lg.login(args.add, args.web)


def open_db(args):
    device_id = select_device()

    ls_files = "ls -lhS ./files"
    select_columns = "awk '{print $8, $5, $6, $7}'"
    keep_db = "grep -x 'Mailbox-.*realm\s.*'"

    result = adb(f"shell run-as com.infomaniak.mail {ls_files} | {select_columns} | {keep_db}", device_id)
    files = remove_empty_items(result.stdout.split("\n"))

    filename = select_in_list("Select database", files).split(" ")[0]

    working_directory = "/tmp/ink_db_pull/"
    if os.path.exists(working_directory):
        shutil.rmtree(working_directory)
    os.makedirs(working_directory, exist_ok=True)

    pull_local_file(f"./files/{filename}", f"{working_directory}/{filename}", device_id)

    subprocess.Popen(("open", working_directory + filename), cwd=None)


def pull_local_dir(src_path, dest_path, device_id):
    result = adb(f"exec-out run-as com.infomaniak.mail ls -1 {src_path}", device_id)
    os.makedirs(dest_path, exist_ok=True)
    files = remove_empty_items(result.stdout.split("\n"))
    for file in files:
        pull_local_file(f"{src_path}/{file}", f"{dest_path}/{file}", device_id)


def pull_local_file(src_path, dest_path, device_id):
    adb(f"exec-out run-as com.infomaniak.mail cat '{src_path}' > {dest_path}", device_id)


def catch_empty_calls(parser):
    return lambda _: parser.print_usage()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()  # (description="Arguments for kmail")
    parser.set_defaults(func=catch_empty_calls(parser))
    subparsers = parser.add_subparsers(help='sub-command help')

    # Databases
    db_parser = subparsers.add_parser("db", help="open or rm databases of the project")
    db_parser.set_defaults(func=catch_empty_calls(db_parser))
    db_subparser = db_parser.add_subparsers(help="db-sub-command help")

    db_clear_parser = db_subparser.add_parser("rm", help="deletes all of the databases containg mails or attachment "
                                                         "cache but keeps the account logged in using adb")
    db_clear_parser.add_argument("-r", "--restart", action="store_true", default=False,
                                 help="also restart the app")
    db_clear_parser.set_defaults(func=clear_mail_db)

    db_open_parser = db_subparser.add_parser("open", help="pulls and open a db file")
    db_open_parser.set_defaults(func=open_db)

    # Show layout bounds
    bounds_parser = subparsers.add_parser("bounds", help="toggles layout bounds for the android device using adb")
    bounds_parser.set_defaults(func=show_layout_bounds)

    # Eml
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

    # Open last video
    last_video_parser = subparsers.add_parser("lastvid",
                                              help="copies last recorded video of the emulator to the desktop")
    last_video_parser.add_argument("-o", "--open", action="store_true", default=False,
                                   help="opens the file in default player at the same time")
    last_video_parser.add_argument("--here", action="store_true", default=False,
                                   help="downloads the file in current directory instead of desktop")
    last_video_parser.set_defaults(func=copy_last_video)

    # Loco
    loco_parser = subparsers.add_parser("loco", help="automatically import loco and remove loco's autogenerated header")
    loco_parser.set_defaults(func=update_loco)

    # Login
    login_parser = subparsers.add_parser("login", help="automated the process of logging in")
    login_parser.add_argument("-a", "--add", action="store_true", default=False,
                              help="skip view pager four pages navigation when you add a new account to existing ones")
    login_parser.add_argument("-w", "--web", action="store_true", default=False,
                              help="start login inputs from the webview")
    login_parser.set_defaults(func=login)

    # Actual parsing of the user input
    args = parser.parse_args()
    args.func(args)
