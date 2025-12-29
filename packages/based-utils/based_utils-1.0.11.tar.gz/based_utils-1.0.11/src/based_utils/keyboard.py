from typing import TYPE_CHECKING

from pynput import keyboard

if TYPE_CHECKING:
    from pynput.keyboard import Key, KeyCode


def listen_to_keys(*keys: Key | KeyCode) -> dict[Key | KeyCode, bool]:
    keys_pressed = dict.fromkeys(keys, False)

    def on_release(k: Key | KeyCode | None) -> None:
        if k in keys:
            keys_pressed[k] = True

    keyboard.Listener(on_release=on_release, suppress=True).start()
    return keys_pressed
