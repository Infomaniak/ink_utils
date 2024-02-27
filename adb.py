import subprocess

import config
from utils import remove_empty_items, select_in_list


def adb(command_args, device_id, stderr=None):
    return subprocess.run("adb -s " + device_id + " " + command_args,
                          stdout=subprocess.PIPE,
                          stderr=stderr,
                          shell=True,
                          universal_newlines=True)


def select_device():
    out = subprocess.run("adb devices", stdout=subprocess.PIPE, shell=True, universal_newlines=True)
    devices = remove_empty_items(out.stdout.split("\n")[1:])
    return select_in_list("What device would you like to use?", devices).split("\t")[0]


def select_device_or_all(args):
    if args.all_devices:
        device_ids = get_all_devices()
    else:
        device_ids = [select_device()]
    return device_ids


def get_all_devices():
    out = subprocess.run("adb devices", stdout=subprocess.PIPE, shell=True, universal_newlines=True)
    devices = remove_empty_items(out.stdout.split("\n")[1:])
    device_ids = [device.split("\t")[0] for device in devices]
    return device_ids


def close_app(device_id):
    package_name = config.get_project("package", "name")
    adb(f"shell am force-stop {package_name}", device_id)


def open_app(device_id):
    package_name = config.get_project("package", "name")
    adb(f"shell monkey -p {package_name} -c android.intent.category.LAUNCHER 1", device_id, stderr=subprocess.DEVNULL)
