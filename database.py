import os
import shutil
import subprocess

import config as config
import utils
from adb import adb, select_device, close_app, open_app, select_device_or_all, warn_if_current_project_app_is_not_focused, \
    pull_local_file
from utils import remove_empty_items, select_in_list


def clear_mail_db(args):
    default_pattern = get_glob_db_pattern()

    package_name = config.get_project("global", "package_name")

    for device_id in select_device_or_all(args):
        warn_if_current_project_app_is_not_focused(device_id)

        adb(f"exec-out run-as {package_name} find ./files -name '{default_pattern}' -exec rm -r {{}} \\;", device_id)

        if args.restart:
            close_app(device_id)
            open_app(device_id)


def open_db(args):
    device_id = select_device()

    ls_files = "ls -lhS ./files"
    select_columns = "awk '{print $8, $5, $6, $7}'"
    keep_db = f"grep -x '{get_regex_db_pattern()}'"

    package_name = config.get_project("global", "package_name")

    result = adb(f"shell run-as {package_name} {ls_files} | {select_columns} | {keep_db}", device_id)
    files = remove_empty_items(result.stdout.split("\n"))
    aligned_files = align_columns(files)

    filename = select_in_list("Select database", aligned_files).split(" ")[0]

    working_directory = "/tmp/ink_db_pull/"
    utils.create_folder_and_remove_if_exists(working_directory)
    # if os.path.exists(working_directory):
    #     shutil.rmtree(working_directory)
    # os.makedirs(working_directory, exist_ok=True)

    pull_local_file(f"./files/{filename}", f"{working_directory}/{filename}", package_name, device_id)

    subprocess.Popen(("open", working_directory + filename), cwd=None)


def align_columns(files):
    # Split each line into columns
    split_lines = [line.split(" ") for line in files]

    # Find the max width for each column
    col_widths = [max(len(row[i]) for row in split_lines) for i in range(len(split_lines[0]))]

    # Format each line
    formatted_lines = []
    for row in split_lines:
        formatted_line = "  ".join(col.ljust(col_widths[i]) for i, col in enumerate(row))
        formatted_lines.append(formatted_line)

    return formatted_lines


def get_regex_db_pattern():
    return ".*\.realm\s.*"


def get_glob_db_pattern():
    return "*.realm*"


def pull_local_dir(src_path, dest_path, device_id):
    package_name = config.get_project("global", "package_name")

    result = adb(f"exec-out run-as {package_name} ls -1 {src_path}", device_id)
    os.makedirs(dest_path, exist_ok=True)
    files = remove_empty_items(result.stdout.split("\n"))
    for file in files:
        pull_local_file(f"{src_path}/{file}", f"{dest_path}/{file}", package_name, device_id)
