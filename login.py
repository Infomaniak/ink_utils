import getpass
import time

from adb import adb, select_device, open_app
import config as config

sleep_duration = 0.9
login_device_id = None


def login():
    login = config.get("login", "id", None)
    if login is None:
        login = input("Email:")

    pwd = config.get("login", "pwd", None)
    if pwd is None:
        pwd = getpass.getpass()

    global login_device_id
    login_device_id = select_device()

    if not_running():
        open_app(login_device_id)
        time.sleep(1)

    # to_fourth_page
    input_combination("shell input keyevent 61 61 61 61 61 61 61 61 61 66 66 66")

    # click_login
    input_combination("shell input keyevent 61 61 61 61 61 66")

    # focus_email
    input_combination("shell input keyevent 61 61 61")

    # enter_email
    input_combination(f"shell input text {login}")

    # focus_pwd
    input_combination("shell input keyevent 61")

    # enter_pwd
    input_combination(f"shell input text {pwd}")

    # action_login
    input_combination("shell input keyevent 61 61 66")


def input_combination(adb_arguments):
    adb(adb_arguments, login_device_id)
    time.sleep(sleep_duration)


def not_running():
    result = adb("shell pidof com.infomaniak.mail", login_device_id)
    pid = result.stdout
    return pid == ""
