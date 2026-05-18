import itertools
import sys
import threading
import time


class Spinner:
    STYLES = {
        'simple': ['|', '/', '-', '\\'],
        'braille': ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'],
        'arc': ['◐', '◓', '◑', '◒'],
        'dots': ['⢄', '⢂', '⢁', '⡁', '⡈', '⡐', '⡠'],
        'flow': ['▹▹▹▹▹', '▸▹▹▹▹', '▹▸▹▹▹', '▹▹▸▹▹', '▹▹▹▸▹', '▹▹▹▹▸'],
        'clock': ['🕐', '🕑', '🕒', '🕓', '🕔', '🕕', '🕖', '🕗', '🕘', '🕙', '🕚', '🕛'],
        'stars': ['·', '✻', '✽', '✶', '✳', '✢'],
    }

    def __init__(self, message="Processing…", style='clock'):
        self.message = message
        self.frames = self.STYLES.get(style, self.STYLES['simple'])
        self.stop_event = threading.Event()
        self.thread = None

    def start(self):
        self.thread = threading.Thread(target=self._spin, daemon=True)
        self.thread.start()

    def _spin(self):
        spinner = itertools.cycle(self.frames)
        while not self.stop_event.is_set():
            sys.stdout.write(f'\r{next(spinner)} {self.message}')
            sys.stdout.flush()
            time.sleep(0.1)  # Lower this (e.g., 0.05) for faster animation
        sys.stdout.write(f'\r✓ {self.message} Done!        \n')
        sys.stdout.flush()

    def stop(self):
        self.stop_event.set()
        if self.thread:
            self.thread.join()
