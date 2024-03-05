#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK

import argparse
import glob
import pathlib
import subprocess

import config
import database as db
import eml_writer as ew
import loco_updater as lu
import login as lg
import projects
from adb import adb, select_device
from adb_prop import show_layout_bounds, show_layout_bars
from updater import check_for_updates, rm_cache as update_rm_cache
from utils import select_in_list, accept_substitution


def generate_eml(args):
    html = accept_substitution(args.html)
    ew.new_eml(args.subject, args.sender, args.to, args.cc, html)


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
    if not args.check:
        successfully_updated = lu.update_loco()
        if not successfully_updated:
            exit()
        print()

    print("Searching for errors in imported strings")
    error_count = lu.validate_strings()
    if error_count == 0:
        print("Found no error")
    else:
        accord = "s" if error_count > 1 else ""
        print(f"\nFound {error_count} error{accord}")


def login(args):
    lg.login(args.add, args.web, args.from_email)


def force_dark_mode(args):
    device_id = select_device()
    set_dark_mode("yes", device_id)


def force_light_mode(args):
    device_id = select_device()
    set_dark_mode("no", device_id)


def toggle_dark_light_mode(args):
    device_id = select_device()

    result = adb('shell "cmd uimode night"', device_id)

    is_night_mode_output = result.stdout.strip()
    start_index = is_night_mode_output.rindex(": ") + 2

    is_night_mode = is_night_mode_output[start_index:] == "yes"
    next_state = "no" if is_night_mode else "yes"

    set_dark_mode(next_state, device_id)


def set_dark_mode(yes_or_no, device_id):
    adb(f'shell "cmd uimode night {yes_or_no}"', device_id)


def extract_apk(args):
    optional_grep = "" if args.keyword is None else f" | grep {args.keyword}"
    find_packages_command = f"shell pm list packages -f{optional_grep}"

    device_id = select_device()
    raw_output = adb(find_packages_command, device_id).stdout.strip().splitlines()

    packages = []
    for line in raw_output:
        if line.__contains__("/base.apk="):
            packages.append(line.split("/base.apk=")[-1])

    selected_package = select_in_list("Choose package to extract", packages)

    apk_paths_list = f"shell 'pm path {selected_package}'"
    paths = adb(apk_paths_list, device_id).stdout.strip().splitlines()
    if len(paths) != 1:
        print("Bundled APK encountered. Cannot proceed\n")
        print("Found:")
        for path in paths:
            print(path)
        return

    download_apk_command = f"shell 'cat `pm path {selected_package} | cut -d':' -f2`' > {selected_package}.apk"
    adb(download_apk_command, device_id)

    print("Extraction finished")


def rm_cache(args):
    update_rm_cache()


def manage_projects(args):
    if args.selected_project is not None:
        projects.select_project(args.selected_project)
    else:
        projects.list_projects()


def manually_install_apk(args):
    device_id = select_device()
    project_path = config.get_project("loco", "project_root")  # Make it a global setting not a loco one
    apk_folder = f"{project_path}/build/intermediates/apk/standard/debug"

    files_paths = glob.glob(apk_folder + "/*")
    for file_path in files_paths:
        if file_path.endswith(".apk"):
            print(f"installing {file_path}")
            adb(f'install -t "{file_path}"', device_id)
            break


def catch_empty_calls(parser):
    return lambda _: parser.print_usage()


def add_all_device_arg(parser):
    parser.add_argument("-ad", "--all-devices", action="store_true", default=False, help="apply to all connected devices")


def define_commands(parser):
    subparsers = parser.add_subparsers(help='sub-command help')

    # Databases
    db_parser = subparsers.add_parser("db", help="open or rm databases of the project")
    db_parser.set_defaults(func=catch_empty_calls(db_parser))
    db_subparser = db_parser.add_subparsers(help="db-sub-command help")
    db_clear_parser = db_subparser.add_parser("rm", help="deletes all of the databases containg mails or attachment "
                                                         "cache but keeps the account logged in using adb")
    db_clear_parser.add_argument("-r", "--restart", action="store_true", default=False,
                                 help="also restart the app")
    add_all_device_arg(db_clear_parser)
    db_clear_parser.add_argument("-m", "--mailbox", action="store_true", default=False,
                                 help="removes mailbox content databases")
    db_clear_parser.add_argument("-mi", "-i", "--mailbox-info", action="store_true", default=False,
                                 help="removes mailbox info databases")
    db_clear_parser.add_argument("-u", "--user", action="store_true", default=False,
                                 help="removes user info databases")
    db_clear_parser.add_argument("-c", "--coil", action="store_true", default=False,
                                 help="removes coil caches")
    db_clear_parser.add_argument("-n", "--network", action="store_true", default=False,
                                 help="removes network caches")
    db_clear_parser.add_argument("-e", "--everything", action="store_true", default=False,
                                 help="remove all of the possible files")
    db_clear_parser.set_defaults(func=db.clear_mail_db)
    db_open_parser = db_subparser.add_parser("open", help="pulls and open a db file")
    db_open_parser.add_argument("-u", "--user", action="store_true", default=False, help="open users databases")
    db_open_parser.add_argument("-mi", "-i", "--mailbox-info", action="store_true", default=False,
                                help="open mailbox info databases")
    db_open_parser.set_defaults(func=db.open_db)

    # Show layout bounds
    bounds_parser = subparsers.add_parser("bounds", help="toggles layout bounds for the android device using adb")
    add_all_device_arg(bounds_parser)
    bounds_parser.set_defaults(func=show_layout_bounds)

    # Eml
    eml_parser = subparsers.add_parser("eml", help="creates an eml file in the current directory")
    eml_parser.add_argument("html", nargs="?", help="html code of the content of the mail")
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
    loco_parser.add_argument("-c", "--check", action="store_true", default=False,
                             help="only checks if strings in the project are correctly formatted but do not import")
    loco_parser.set_defaults(func=update_loco)

    # Login
    login_parser = subparsers.add_parser("login", help="automated the process of logging in")
    login_parser.add_argument("-a", "--add", action="store_true", default=False,
                              help="skip view pager four pages navigation when you add a new account to existing ones")
    login_parser.add_argument("-w", "--web", action="store_true", default=False,
                              help="start login inputs from the webview")
    login_parser.add_argument("-e", "--from-email", action="store_true", default=False,
                              help="start login inputs from when the email field is focused")
    login_parser.set_defaults(func=login)

    # Dark mode
    dark_mode_parser = subparsers.add_parser("color", help="changes dark and light mode")
    dark_mode_parser.set_defaults(func=catch_empty_calls(dark_mode_parser))
    color_subparser = dark_mode_parser.add_subparsers(help="dark mode help")
    dark_parser = color_subparser.add_parser("dark", help="sets dark mode")
    dark_parser.set_defaults(func=force_dark_mode)
    light_parser = color_subparser.add_parser("light", help="sets light mode")
    light_parser.set_defaults(func=force_light_mode)
    toggle_parser = color_subparser.add_parser("toggle", help="toggles the current dark mode")
    toggle_parser.set_defaults(func=toggle_dark_light_mode)

    # Apk extraction
    apk_extraction_parser = subparsers.add_parser("apk", help="extract an installed apk")
    apk_extraction_parser.add_argument("keyword", nargs="?", help="only propose package names that contains this given string")
    apk_extraction_parser.set_defaults(func=extract_apk)

    # Cache management
    cache_parser = subparsers.add_parser("cache", help="manage the cache of ink")
    cache_parser.set_defaults(func=catch_empty_calls(cache_parser))
    color_subparser = cache_parser.add_subparsers(help="cache help")
    dark_parser = color_subparser.add_parser("rm", help="resets the cache")
    dark_parser.set_defaults(func=rm_cache)

    # Project management
    project_parser = subparsers.add_parser("project",
                                           help="manages projects defined in settings. If no arg is supplied, lists the projects")
    project_parser.add_argument("selected_project", nargs="?", help="the project to select for future uses")
    project_parser.set_defaults(func=manage_projects)
    project_subparser = project_parser.add_subparsers()
    manual_install_parser = project_subparser.add_parser("install", help="manually installs the built debug apk")
    manual_install_parser.set_defaults(func=manually_install_apk)

    # Show gpu processing bars
    bounds_parser = subparsers.add_parser("bars", help="toggles visual bars for the android device using adb")
    add_all_device_arg(bounds_parser)
    bounds_parser.set_defaults(func=show_layout_bars)


if __name__ == '__main__':
    check_for_updates()

    parser = argparse.ArgumentParser()  # (description="Arguments for kmail")
    parser.set_defaults(func=catch_empty_calls(parser))

    define_commands(parser)

    # Actual parsing of the user input
    args = parser.parse_args()
    args.func(args)
