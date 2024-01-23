import os.path
import random
import subprocess
from datetime import datetime, timedelta

CACHE_FILE = "updater_cache"


def run_cmd(cmd):
    out = subprocess.run(cmd, stdout=subprocess.PIPE, shell=True, universal_newlines=True)
    return out.stdout


def does_current_branch_target_main():
    return run_cmd("git rev-parse --abbrev-ref HEAD@{upstream}").startswith("origin/main")


def get_current_branch_hash():
    return run_cmd("git rev-parse HEAD").strip()


def get_remote_main_hash():
    remote_hash = run_cmd("git fetch && git rev-parse origin/main").strip()
    cache_remote_hash(remote_hash)
    return remote_hash


def is_cache_outdated():
    if not os.path.isfile(CACHE_FILE):
        return True

    with open(CACHE_FILE, "r") as fd:
        lines = fd.readlines()

    if len(lines) < 2:
        return True

    date = lines[0].strip()
    last_check = datetime.fromisoformat(date)
    validity_limit = last_check + timedelta(days=1)

    return datetime.now() > validity_limit


def read_cached_remote_hash():
    with open(CACHE_FILE, "r") as fd:
        lines = fd.readlines()

    return lines[1].strip()


def cache_remote_hash(remote_hash):
    with open(CACHE_FILE, "w+") as fd:
        fd.write(datetime.now().isoformat() + "\n" + remote_hash)


def check_for_updates():
    if does_current_branch_target_main():
        if is_cache_outdated():
            latest_hash = get_remote_main_hash()
        else:
            latest_hash = read_cached_remote_hash()

        current_hash = get_current_branch_hash()

        if current_hash != latest_hash:
            if random.randint(0, 31) == 0:
                rainbow_print("A new version of Ink is available!\n")
            else:
                print(color("A new version of Ink is available!\n", Colors.blue))


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
