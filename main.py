#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK

import argparse
import glob
import pathlib
import signal
import subprocess
import sys

import config
import database as db
import eml_writer as ew
import font_size
import loco_updater as lu
import login as lg
import navbar_mode
import projects
from adb import adb, select_device, close_app, open_app, select_device_or_all, warn_if_current_project_app_is_not_focused
from adb_prop import show_layout_bounds, show_layout_bars
from updater import check_for_updates, rm_cache as update_rm_cache, update_git_project, update_cmd
from utils import select_in_list, accept_substitution, ink_folder, cancel_ink_command


def generate_eml(args):
    html = accept_substitution(args.html)
    ew.new_eml(args.subject, args.sender, args.to, args.cc, args.with_date, html)


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
    project_root = config.get_project("global", "project_root")
    res_folder_path = "/src/main/res"

    loco_update_strategy = lu.LocoUpdateStrategy(
        # If only checking strings validity, no need to raise an error for a missing loco api key
        api_key=config.get_project("loco", "loco_key", raise_error=not args.check),
        copy_target_folder=project_root + res_folder_path,
    )

    import_strings(args, loco_update_strategy, args.tag)


def update_loco_core(args):
    project_root = config.get_project("global", "project_root")
    res_folder_path = "/src/main/res"

    loco_update_strategy = lu.LocoUpdateStrategy(
        # If only checking strings validity, no need to raise an error for a missing loco api key
        api_key=config.get_global("loco", "core_key", raise_error=not args.check),
        copy_target_folder=project_root + "/../Core" + res_folder_path,
    )

    import_strings(args, loco_update_strategy, args.tag)


def import_strings(args, loco_update_strategy, feature_tag):
    if not args.check:
        successfully_updated = lu.update_loco(args.target_ids, loco_update_strategy, feature_tag)
        if not successfully_updated:
            exit(1)
        print()

    print("Searching for errors in imported strings")
    error_count = lu.validate_strings(loco_update_strategy)
    if error_count == 0:
        print("Found no error")
    else:
        accord = "s" if error_count > 1 else ""
        print(f"\nFound {error_count} error{accord}")
        if args.verbose:
            print("\n[verbose]")
            print("To fix this issue:")
            print("  • Correct the strings and re-import translations into the project.")
            print("  • If this is a false positive, add the string ID as an exception in loco_validator/validator.py, "
                  "then confirm with the project maintainers.")
        exit(1)


def login(args):
    lg.login(args.add, args.web, args.from_email)


def force_dark_mode(args):
    for device_id in select_device_or_all(args):
        set_dark_mode("yes", device_id)


def force_light_mode(args):
    for device_id in select_device_or_all(args):
        set_dark_mode("no", device_id)


def toggle_dark_light_mode(args):
    for device_id in select_device_or_all(args):
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


def open_settings(args):
    if args.folder:
        subprocess.run(['open', config.script_folder], check=True)
    else:
        subprocess.run(['open', '-t', config.config_file], check=True)


def manually_install_apk(args):
    device_id = select_device()
    project_path = config.get_project("global", "project_root")
    apk_folder = f"{project_path}/build/intermediates/apk/standard/debug"

    files_paths = glob.glob(apk_folder + "/*")
    for file_path in files_paths:
        if file_path.endswith(".apk"):
            print(f"installing {file_path}\n")
            result = adb(f'install -t "{file_path}"', device_id)

            output_lines = result.stdout.strip().splitlines()
            is_success = len(output_lines) > 0 and output_lines[-1].strip() == "Success"
            if is_success:
                print("Successfully installed")

            if args.restart:
                if is_success:
                    close_app(device_id)
                    open_app(device_id)
                else:
                    print("\nCould not open the apk because the installation failed")

            break


def update_ps1(args):
    ps1 = subprocess.check_output(['zsh', '-i', '-c', 'echo $PS1']).decode("utf-8")
    parts = ps1.split("\n")

    get_current_project_code = f"$(cat {ink_folder}/.current_project)"

    parts[0] += f"{ps1_bold('ink:(', 'yellow')}{ps1_bold(get_current_project_code, 'red')}{ps1_bold(')', 'yellow')}"

    new_ps1 = "\n".join(parts)
    print(new_ps1)


def ps1_bold(text, color):
    return "%{$fg_bold[" + color + "]%}" + text + "%{$reset_color%}"


def rm_data(args):
    device_ids = select_device_or_all(args)
    package_name = config.get_project("global", "package_name")

    for device_id in device_ids:
        warn_if_current_project_app_is_not_focused(device_id)

        if args.cache:
            adb(f'shell run-as {package_name} "rm -rf ./cache"', device_id)
        else:
            adb(f"shell pm clear {package_name}", device_id)

        if args.restart:
            open_app(device_id)


def list_data(args):
    device_id = select_device()
    package_name = config.get_project("global", "package_name")

    result = adb(f'shell run-as {package_name} "ls ./cache"', device_id, stderr=subprocess.DEVNULL)
    if result.returncode == 1:
        print("Empty cache")
    else:
        print("=== Cache files ===")
        print(result.stdout)


def update_project(args):
    update_git_project()


def action_view(args):
    devices = select_device_or_all(args)
    package_name = config.get_project("global", "package_name")
    for device in devices:
        adb(f'shell am start -a android.intent.action.VIEW -d "{args.content}" {package_name}', device_id=device)


def print_patch_note(args):
    project_git_path = config.get_project("global", "project_root") + "/.."

    if args.start_git_ref is None and args.short is False:
        subprocess.run(config.script_folder + "/get_latest_merges.sh", cwd=project_git_path)
    elif not (args.start_git_ref is None) and args.short is False:
        subprocess.run((config.script_folder + "/get_latest_merges.sh", args.start_git_ref), cwd=project_git_path)
    elif args.start_git_ref is None and args.short:
        subprocess.run((config.script_folder + "/get_latest_merges.sh", "--short"), cwd=project_git_path)
    else:
        subprocess.run((config.script_folder + "/get_latest_merges.sh", args.start_git_ref, "--short"),
                       cwd=project_git_path)


def force_airplane_on(args):
    device_id = select_device()
    set_airplane_mode("enable", device_id)


def force_airplane_off(args):
    device_id = select_device()
    set_airplane_mode("disable", device_id)


def force_airplane_toggle(args):
    device_id = select_device()

    result = adb('shell cmd connectivity airplane-mode', device_id).stdout.strip()
    is_airplane_enabled = result == "enabled"
    next_state = "disable" if is_airplane_enabled else "enable"
    set_airplane_mode(next_state, device_id)


def set_airplane_mode(enabled_or_disabled, device_id):
    adb(f'shell cmd connectivity airplane-mode {enabled_or_disabled}', device_id)


def signal_handler(sig, frame):
    cancel_ink_command(message_end="", exit_code=130)  # interrupted by user


def catch_empty_calls(parser):
    return lambda _: parser.print_usage()


def add_all_device_arg(parser):
    parser.add_argument("-ad", "--all-devices", action="store_true", default=False, help="apply to all connected devices")


def add_restart_app_arg(parser):
    parser.add_argument("-r", "--restart", action="store_true", default=False, help="also restart the app")


def define_commands(parser):
    subparsers = parser.add_subparsers(help='sub-command help')

    # Databases
    db_parser = subparsers.add_parser("db", help="open or rm databases of the project")
    db_parser.set_defaults(func=catch_empty_calls(db_parser))
    db_subparser = db_parser.add_subparsers(help="db-sub-command help")
    db_clear_parser = db_subparser.add_parser("rm", help="deletes all of the databases containg mails or attachment "
                                                         "cache but keeps the account logged in using adb")
    add_restart_app_arg(db_clear_parser)
    add_all_device_arg(db_clear_parser)
    db_clear_parser.set_defaults(func=db.clear_mail_db)
    db_open_parser = db_subparser.add_parser("open", help="pulls and open a db file")
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
    eml_parser.add_argument("-nd", "--no-date", dest="with_date", action="store_false", default=True,
                            help="do not automatically define a date")
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
    def add_loco_arguments(parser):
        parser.add_argument("-c", "--check", action="store_true", default=False,
                            help="only checks if strings in the project are correctly formatted but do not import")
        parser.add_argument("-v", "--verbose", action="store_true", default=False,
                            help="details steps to solve the issue")
        parser.add_argument("-t", "--tag", dest="tag", help="only pull strings from this tag")
        parser.add_argument("target_ids", nargs="*", help="limit string ids that get added")

    loco_parser = subparsers.add_parser("loco", help="automatically import loco and remove loco's autogenerated header")
    add_loco_arguments(loco_parser)
    loco_parser.set_defaults(func=update_loco)

    # Loco core
    loco_core_parser = subparsers.add_parser("lococore", help="import core's loco project just like the classic loco method")
    add_loco_arguments(loco_core_parser)
    loco_core_parser.set_defaults(func=update_loco_core)

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
    add_all_device_arg(dark_parser)
    dark_parser.set_defaults(func=force_dark_mode)
    light_parser = color_subparser.add_parser("light", help="sets light mode")
    add_all_device_arg(light_parser)
    light_parser.set_defaults(func=force_light_mode)
    toggle_parser = color_subparser.add_parser("toggle", help="toggles the current dark mode")
    add_all_device_arg(toggle_parser)
    toggle_parser.set_defaults(func=toggle_dark_light_mode)

    # Apk extraction
    apk_extraction_parser = subparsers.add_parser("apk", help="extract an installed apk")
    apk_extraction_parser.add_argument("keyword", nargs="?", help="only propose package names that contains this given string")
    apk_extraction_parser.set_defaults(func=extract_apk)

    # Ink's cache management
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

    # Project settings
    settings_parser = subparsers.add_parser("settings", help="opens the settings file")
    settings_parser.add_argument("-f", "--folder", action="store_true", default=False,
                                 help="Only opens the folder containing the file")
    settings_parser.set_defaults(func=open_settings)

    # Manual apk install
    manual_install_parser = subparsers.add_parser("forceinstall", help="manually installs the built debug apk")
    add_restart_app_arg(manual_install_parser)
    manual_install_parser.set_defaults(func=manually_install_apk)

    # Show gpu processing bars
    bounds_parser = subparsers.add_parser("bars", help="toggles visual bars for the android device using adb")
    add_all_device_arg(bounds_parser)
    bounds_parser.set_defaults(func=show_layout_bars)

    # Update PS1 to display current selected project
    ps1_parser = subparsers.add_parser("ps1", help="update PS1 to display current selected project")
    ps1_parser.set_defaults(func=update_ps1)

    # Remove data of the app
    data_parser = subparsers.add_parser("data", help="remove data or cache of the app")
    data_parser.set_defaults(func=catch_empty_calls(data_parser))
    data_subparser = data_parser.add_subparsers(help="data help")

    rm_data_parser = data_subparser.add_parser("rm", help="removes data or cache of the selected project")
    rm_data_parser.add_argument("-c", "--cache", action="store_true", default=False,
                                help="only removes the cache")
    add_restart_app_arg(rm_data_parser)
    add_all_device_arg(rm_data_parser)
    rm_data_parser.set_defaults(func=rm_data)

    list_data_parser = data_subparser.add_parser("list", help="lists files inside the cache of the selected project")
    list_data_parser.set_defaults(func=list_data)

    # Update by pulling the latest version of master on the git project
    update_parser = subparsers.add_parser(update_cmd, help="update by pulling the latest version of master on the git project")
    update_parser.set_defaults(func=update_project)

    # Set emulator font size
    font_size_parser = subparsers.add_parser("font",
                                             help="set emulator font size value in {small|min, normal|default|reset, large, largest|max}")
    font_size_parser.add_argument("size", type=font_size.FontSize.from_string, choices=list(font_size.FontSize))
    add_all_device_arg(font_size_parser)
    font_size_parser.set_defaults(func=font_size.change_font_size)

    # Action VIEW for an url, mainly for deeplinks
    action_view_parser = subparsers.add_parser("view",
                                               help="sends an ACTION_VIEW intent to the app with the provided argument. Mainly for deeplings")
    action_view_parser.add_argument("content", nargs="?")
    add_all_device_arg(action_view_parser)
    action_view_parser.set_defaults(func=action_view)

    # Pretty prints all PRs that got merged inside master since last version
    action_view_parser = subparsers.add_parser("patchnote",
                                               help="pretty prints all PRs that got merged inside master since last version")
    action_view_parser.add_argument("start_git_ref", nargs="?",
                                    help="any valid git ref. The command will compare remote master to this git ref if provided, else it detects the biggest tag automatically")
    action_view_parser.add_argument("-s", "--short", action="store_true", default=False,
                                    help="prints in a more compact manner")
    action_view_parser.set_defaults(func=print_patch_note)

    # Sets airplane mode
    airplane_mode_parser = subparsers.add_parser("airplane", help="set the airplane mode of the emulator")
    airplane_mode_parser.set_defaults(func=catch_empty_calls(airplane_mode_parser))
    airplane_mode_subparser = airplane_mode_parser.add_subparsers(help="airplane mode help")
    airplane_mode_on_parser = airplane_mode_subparser.add_parser("on", help="enable airplane mode")
    airplane_mode_on_parser.set_defaults(func=force_airplane_on)
    airplane_mode_off_parser = airplane_mode_subparser.add_parser("off", help="disable airplane mode")
    airplane_mode_off_parser.set_defaults(func=force_airplane_off)
    airplane_mode_toggle_parser = airplane_mode_subparser.add_parser("toggle", help="toggle airplane mode enabled state")
    airplane_mode_toggle_parser.set_defaults(func=force_airplane_toggle)

    # Change navbar gesture modes
    navbar_mode_parser = subparsers.add_parser("navbar", help="set the navigation bar style between 3 buttons and gestures")
    navbar_mode_parser.add_argument("mode", type=navbar_mode.NavbarMode.from_string, choices=list(navbar_mode.NavbarMode))
    add_all_device_arg(navbar_mode_parser)
    navbar_mode_parser.set_defaults(func=navbar_mode.set_navbar_mode)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)

    raw_args = ' '.join(sys.argv[1:])
    check_for_updates(raw_args)

    parser = argparse.ArgumentParser()  # (description="Arguments for kmail")
    parser.set_defaults(func=catch_empty_calls(parser))

    define_commands(parser)

    # Actual parsing of the user input
    args = parser.parse_args()
    args.func(args)
