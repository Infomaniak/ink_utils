import subprocess

import config
from utils import remove_empty_items, select_in_list, cancel_ink_command


def adb(command_args, device_id, stderr=None):
    command = "adb -s " + device_id + " " + command_args
    # print("Executing command:", command)
    return subprocess.run(command,
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
    package_name = config.get_project("global", "package_name")
    adb(f"shell am force-stop {package_name}", device_id)


def open_app(device_id):
    package_name = config.get_project("global", "package_name")
    adb(f"shell monkey -p {package_name} -c android.intent.category.LAUNCHER 1", device_id, stderr=subprocess.DEVNULL)


def get_focused_app_package_name(device_id):
    return adb(
        r"shell dumpsys activity activities | grep -E 'mFocusedApp' | sed -E 's/.* ([^ ]+)\/.*/\1/'",
        device_id,
    ).stdout.strip()


# If one of our application is focused but the currently checked out project is different, ask confirmation from the user before
# executing the rest of the code
def warn_if_current_project_app_is_not_focused(device_id):
    focused_package_name = get_focused_app_package_name(device_id)
    if not focused_package_name.startswith("com.infomaniak"):
        return

    selected_package_name = config.get_project("global", "package_name")
    if focused_package_name != selected_package_name:
        choice = select_in_list("Current project is different from focused app. Continue anyway?", ["Yes", "No"])
        if choice == "No":
            cancel_ink_command()
