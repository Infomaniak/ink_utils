from enum import Enum

from adb import adb, select_device_or_all


def change_font_size(args):
    for device_id in select_device_or_all(args):
        adb(f'shell settings put system font_scale {args.size.value}', device_id)


class FontSize(Enum):
    min = 0.85
    small = 0.85
    default = 1
    normal = 1
    reset = 1
    large = 1.15
    max = 1.3
    largest = 1.3

    def __str__(self):
        return self.name

    @staticmethod
    def from_string(s):
        try:
            return FontSize[s]
        except KeyError:
            raise ValueError()
