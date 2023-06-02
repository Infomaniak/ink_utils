import subprocess
import inquirer

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

    if len(devices) == 1:
        return devices[0].split("\t")[0]

    return select_in_list("What device would you like to use?", devices).split("\t")[0]


def close_app(device_id):
    adb("shell am force-stop com.infomaniak.mail", device_id)


def open_app(device_id):
    adb("shell monkey -p com.infomaniak.mail -c android.intent.category.LAUNCHER 1", device_id,
        stderr=subprocess.DEVNULL)
