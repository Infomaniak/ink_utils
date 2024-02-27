import os
import shutil
import subprocess

import config as config
from adb import adb, select_device, close_app, open_app, select_device_or_all
from utils import remove_empty_items, select_in_list


def clear_mail_db(args):
    if not (args.mailbox or args.mailbox_info or args.user or args.coil or args.network or args.everything):
        print("No target specified. Fallback on removing mailboxes")
        args.mailbox = True

    package_name = config.get_project("package", "name")

    for device_id in select_device_or_all(args):
        if args.mailbox or args.everything:
            adb(f"exec-out run-as {package_name} find ./files -name 'Mailbox-*-*.realm*' -exec rm -r {{}} \\;", device_id)

        if args.mailbox_info or args.everything:
            adb(f"exec-out run-as {package_name} find ./files -name 'MailboxInfo.realm*' -exec rm -r {{}} \\;", device_id)

        if args.user or args.everything:
            adb(f"exec-out run-as {package_name} find ./files -name 'User-*.realm*' -exec rm -r {{}} \\;", device_id)

        if args.coil or args.everything:
            adb(f"exec-out run-as {package_name} find ./cache -name '*_cache' -exec rm -r {{}} \\;", device_id)

        if args.network or args.everything:
            adb(f"exec-out run-as {package_name} find ./files -name 'network-response-body-*' -exec rm {{}} \\;", device_id)

        if args.restart:
            close_app(device_id)
            open_app(device_id)


def open_db(args):
    device_id = select_device()

    ls_files = "ls -lhS ./files"
    select_columns = "awk '{print $8, $5, $6, $7}'"
    keep_db = f"grep -x '{get_db_pattern(args)}'"

    package_name = config.get_project("package", "name")

    result = adb(f"shell run-as {package_name} {ls_files} | {select_columns} | {keep_db}", device_id)
    files = remove_empty_items(result.stdout.split("\n"))

    filename = select_in_list("Select database", files).split(" ")[0]

    working_directory = "/tmp/ink_db_pull/"
    if os.path.exists(working_directory):
        shutil.rmtree(working_directory)
    os.makedirs(working_directory, exist_ok=True)

    pull_local_file(f"./files/{filename}", f"{working_directory}/{filename}", package_name, device_id)

    subprocess.Popen(("open", working_directory + filename), cwd=None)


def get_db_pattern(args):
    if args.user:
        return "User-.*realm\s.*"
    elif args.mailbox_info:
        return "MailboxInfo.realm\s.*"
    else:
        return "Mailbox-.*realm\s.*"


def pull_local_dir(src_path, dest_path, device_id):
    package_name = config.get_project("package", "name")

    result = adb(f"exec-out run-as {package_name} ls -1 {src_path}", device_id)
    os.makedirs(dest_path, exist_ok=True)
    files = remove_empty_items(result.stdout.split("\n"))
    for file in files:
        pull_local_file(f"{src_path}/{file}", f"{dest_path}/{file}", package_name, device_id)


def pull_local_file(src_path, dest_path, package_name, device_id):
    adb(f"exec-out run-as {package_name} cat '{src_path}' > {dest_path}", device_id)
