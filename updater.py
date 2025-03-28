import os.path
import random
import subprocess
from datetime import datetime

from utils import ink_folder

cache_file = ink_folder + "/updater_cache"

update_cmd = "update"


def run_git_local_cmd(cmd):
    out = subprocess.run(cmd, stdout=subprocess.PIPE, shell=True, universal_newlines=True, cwd=ink_folder)
    return out.stdout


def does_current_branch_target_main():
    return run_git_local_cmd("git rev-parse --abbrev-ref HEAD@{upstream}").startswith("origin/main")


def get_current_branch_hash():
    return run_git_local_cmd("git rev-parse HEAD").strip()


def get_remote_main_hash():
    remote_hash = run_git_local_cmd("git fetch && git rev-parse origin/main").strip()
    cache_remote_hash(remote_hash)
    return remote_hash


def is_cache_outdated():
    if not os.path.isfile(cache_file):
        return True

    with open(cache_file, "r") as fd:
        lines = fd.readlines()

    if len(lines) < 2:
        return True

    date = lines[0].strip()
    last_check = datetime.fromisoformat(date)

    return datetime.now().date() > last_check.date()


def read_cached_remote_hash():
    with open(cache_file, "r") as fd:
        lines = fd.readlines()

    return lines[1].strip()


def cache_remote_hash(remote_hash):
    with open(cache_file, "w+") as fd:
        fd.write(datetime.now().isoformat() + "\n" + remote_hash)


def check_for_updates(raw_args):
    if raw_args == update_cmd:  # Do not check if there's an available update when the user is explicitly asking to update
        return

    if does_current_branch_target_main():
        if is_cache_outdated():
            latest_hash = get_remote_main_hash()
        else:
            latest_hash = read_cached_remote_hash()

        current_hash = get_current_branch_hash()

        if current_hash != latest_hash:
            if random.randint(0, 15) == 0:
                rainbow_print("A new version of Ink is available!\n")
            else:
                print(color("A new version of Ink is available!\n", Colors.blue))


def update_git_project():
    if does_current_branch_target_main():
        run_git_local_cmd("git pull")
    else:
        print("Your current branch does not target main")


def rm_cache():
    os.remove(cache_file)


# Print utils

def rainbow_print(string):
    colors = [
        Colors.red,
        Colors.orange,
        Colors.yellow,
        Colors.green,
        Colors.blue,
        Colors.purple,
        Colors.white,
    ]

    color_count = len(colors)

    output = ""
    for i in range(len(string)):
        output += color(string[i], colors[i % color_count])

    print(output)


def color(text, rgb):
    return "\033[38;2;{};{};{}m{}\033[0m".format(
        str(rgb[0]), str(rgb[1]), str(rgb[2]), text
    )


class Colors:
    red = (245, 90, 66)
    orange = (245, 170, 66)
    yellow = (245, 252, 71)
    green = (92, 252, 71)
    blue = (71, 177, 252)
    purple = (189, 71, 252)
    white = (255, 255, 255)
