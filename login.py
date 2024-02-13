import getpass
import time

import config as config
from adb import adb, select_device, open_app

sleep_duration = 0.9
login_page_sleep_duration = 1.5
login_device_id = None


def login(skip_view_pager, from_web_view, already_in_email):
    login = config.get_global("login", "id", raise_error=False)
    if login is None:
        login = input("Email:")

    pwd = config.get_global("login", "pwd", raise_error=False)
    if pwd is None:
        pwd = getpass.getpass()

    global login_device_id
    login_device_id = select_device()

    not_skipping_a_step = not already_in_email and not from_web_view and not skip_view_pager
    if not_skipping_a_step and not_running():
        open_app(login_device_id)
        time.sleep(1)

    if not already_in_email:
        if not from_web_view:
            if not skip_view_pager:
                # to_fourth_page
                input_combination("shell input keyevent 61 61 61 61 61 61 61 61 61 66 66 66")

            # click_login
            input_combination("shell input keyevent 61 61 61 61 61 66", login_page_sleep_duration)

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


def input_combination(adb_arguments, custom_sleep_duration=sleep_duration):
    adb(adb_arguments, login_device_id)
    time.sleep(custom_sleep_duration)


def not_running():
    package_name = config.get_project("package", "name")
    result = adb(f"shell pidof {package_name}", login_device_id)
    pid = result.stdout
    return pid == ""
