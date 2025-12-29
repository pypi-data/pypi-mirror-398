from collections import defaultdict
from time import perf_counter_ns

from pynput import keyboard
from pynput.keyboard import Key, KeyCode  # noqa: TC002


def listen_to_keys(*keys: Key | KeyCode) -> dict[Key | KeyCode, list[int]]:
    keys_pressed: dict[Key | KeyCode, list[int]] = defaultdict(list)
    keys_pressed |= {key: [] for key in keys}
    start = perf_counter_ns()

    def on_release(k: Key | KeyCode | None) -> None:
        if k and (not keys or k in keys):
            keys_pressed[k].append(perf_counter_ns() - start)

    keyboard.Listener(on_release=on_release, suppress=True).start()
    return keys_pressed
