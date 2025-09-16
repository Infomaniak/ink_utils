from enum import Enum

from adb import adb, select_device_or_all


def set_navbar_mode(args):
    for device_id in select_device_or_all(args):
        if args.mode == NavbarMode.gesture:
            adb(f'shell cmd overlay disable {NavbarMode.buttons.value}', device_id)
            adb(f'shell cmd overlay enable {NavbarMode.gesture.value}', device_id)
        else:
            adb(f'shell cmd overlay disable {NavbarMode.gesture.value}', device_id)
            adb(f'shell cmd overlay enable {NavbarMode.buttons.value}', device_id)


class NavbarMode(Enum):
    gesture = "com.android.internal.systemui.navbar.gestural"
    buttons = "com.android.internal.systemui.navbar.threebutton"

    def __str__(self):
        return self.name

    @staticmethod
    def from_string(s):
        try:
            return NavbarMode[s]
        except KeyError:
            raise ValueError()
