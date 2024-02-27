import random

from adb import adb, select_device_or_all


def _set_prop(prop_name, value_on, value_off, device_id):
    result = adb(f"shell getprop {prop_name}", device_id)
    # print("When getting current prop state we get: [" + result.stdout.strip() + "]")
    new_layout_state = value_off if (result.stdout.strip() == value_on) else value_on
    # print(f"Setting show {prop_name} to " + new_layout_state)
    adb(f"shell setprop {prop_name} " + new_layout_state, device_id)
    adb("shell service call activity 1599295570", device_id)


def set_prop(args, prop_name, value_on, value_off):
    for device_id in select_device_or_all(args):
        _set_prop(prop_name, value_on, value_off, device_id)


def show_layout_bounds(args):
    set_prop(args, "debug.layout", "true", "false")


def show_layout_bars(args):
    if random.randint(0, 4) == 0:
        spit_bars()
    set_prop(args, "debug.hwui.profile", "visual_bars", "false")


def spit_bars():
    bars = [
        "I code with such precision, bugs flee in submission, call it my byte-sized rendition.",
        "My programming skills are so advanced, even AI asks for my assistance",
        "I code like Mozart composing symphonies, each line a masterpiece in digital harmonies.",
        "I'm like a programmer with a vendetta, erasing bugs like it's code amnesia.",
        "My programming prowess is like a fine wine, improving with age, getting better line by line.",
        "My code's so clean, it's like poetry in motion, executing functions with perfect devotion.",
        "I debug with the precision of a surgeon's knife, slicing through errors to bring code to life.",
        "I code with the finesse of a chef crafting a masterpiece, each line a flavor, every function a feast.",
        "In the labyrinth of code, I'm the Minotaur, navigating complexities with cunning and valor.",
        "I'm the code wizard, weaving spells with syntax, turning bytes into magic with each and every matrix.",
        "My codebase is a garden of innovation, where bugs are but weeds in need of eradication.",
        "In the quantum realm of programming, I'm the entangled mind, deciphering complexities with quantum grind.",
    ]

    print(random.choice(bars), end="\n\n")
