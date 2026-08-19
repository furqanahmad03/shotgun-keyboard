#!/usr/bin/env python3
"""Play sound effects in response to global keyboard input."""

from __future__ import annotations

from pathlib import Path
import os
import select
import string
import sys

# Keep pygame's startup message out of this command-line program.
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame


ASSETS_DIR = Path(__file__).resolve().parent / "assets"
GUN_SOUND_PATH = ASSETS_DIR / "gun.mp3"
BOMB_SOUND_PATH = ASSETS_DIR / "blast.mp3"
LOAD_SOUND_PATH = ASSETS_DIR / "load.mp3"


def load_sounds() -> tuple[
    pygame.mixer.Sound, pygame.mixer.Sound, pygame.mixer.Sound
]:
    sound_paths = (GUN_SOUND_PATH, BOMB_SOUND_PATH, LOAD_SOUND_PATH)
    missing = [path for path in sound_paths if not path.is_file()]
    if missing:
        names = ", ".join(str(path) for path in missing)
        raise FileNotFoundError(f"Missing audio file(s): {names}")

    try:
        pygame.mixer.init()
        # Allow several rapid key presses to play concurrently.
        pygame.mixer.set_num_channels(32)
        return (
            pygame.mixer.Sound(GUN_SOUND_PATH),
            pygame.mixer.Sound(BOMB_SOUND_PATH),
            pygame.mixer.Sound(LOAD_SOUND_PATH),
        )
    except pygame.error as exc:
        pygame.mixer.quit()
        raise RuntimeError(f"Could not initialize audio or load an MP3: {exc}") from exc


def play(sound: pygame.mixer.Sound) -> None:
    """Play without blocking; reuse the oldest channel if all are busy."""
    channel = pygame.mixer.find_channel(force=True)
    if channel is not None:
        channel.play(sound)


def listen_with_pynput(
    gun_sound: pygame.mixer.Sound,
    bomb_sound: pygame.mixer.Sound,
    load_sound: pygame.mixer.Sound,
) -> None:
    """Listen globally on macOS and Windows."""
    from pynput import keyboard

    def on_press(key) -> bool | None:
        if key == keyboard.Key.esc:
            return False

        if key == keyboard.Key.enter:
            play(bomb_sound)
            return None

        if key in (keyboard.Key.backspace, keyboard.Key.space):
            play(load_sound)
            return None

        char = getattr(key, "char", None)
        if char is not None and len(char) == 1 and (
            "a" <= char.lower() <= "z" or "0" <= char <= "9"
        ):
            play(gun_sound)

        return None

    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()


def listen_with_evdev(
    gun_sound: pygame.mixer.Sound,
    bomb_sound: pygame.mixer.Sound,
    load_sound: pygame.mixer.Sound,
) -> None:
    """Listen through Linux input devices, including under Wayland."""
    from evdev import InputDevice, ecodes, list_devices

    letter_codes = {
        getattr(ecodes, f"KEY_{letter}") for letter in string.ascii_uppercase
    }
    digit_codes = {getattr(ecodes, f"KEY_{digit}") for digit in string.digits}
    digit_codes.update(getattr(ecodes, f"KEY_KP{digit}") for digit in string.digits)

    devices = []
    inaccessible = []
    for path in list_devices():
        try:
            device = InputDevice(path)
            key_codes = set(device.capabilities().get(ecodes.EV_KEY, []))
        except PermissionError:
            inaccessible.append(path)
            continue

        # Ignore mice, power buttons, and other devices that expose only a few keys.
        if len(key_codes & letter_codes) >= 10 and ecodes.KEY_ENTER in key_codes:
            devices.append(device)
        else:
            device.close()

    if not devices:
        if inaccessible:
            raise PermissionError(
                "Cannot read Linux keyboard devices. Grant your user access to "
                "/dev/input/event* as described in README.md, then log out and back in."
            )
        raise RuntimeError("No Linux keyboard input device was found.")

    names = ", ".join(device.name or device.path for device in devices)
    print(f"Linux keyboard device(s): {names}")

    try:
        while True:
            readable, _, _ = select.select(devices, [], [])
            for device in readable:
                for event in device.read():
                    # 1 is a new key press; 2 is the normal held-key repeat event.
                    if event.type != ecodes.EV_KEY or event.value not in (1, 2):
                        continue

                    if event.code == ecodes.KEY_ESC:
                        return
                    if event.code in (ecodes.KEY_ENTER, ecodes.KEY_KPENTER):
                        play(bomb_sound)
                    elif event.code in (ecodes.KEY_BACKSPACE, ecodes.KEY_SPACE):
                        play(load_sound)
                    elif event.code in letter_codes or event.code in digit_codes:
                        play(gun_sound)
    finally:
        for device in devices:
            device.close()


def main() -> int:
    try:
        gun_sound, bomb_sound, load_sound = load_sounds()
    except (FileNotFoundError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print("Listening globally. Press Esc to quit.")
    try:
        # Linux uses evdev so native Wayland applications are captured.
        # macOS and Windows use pynput's native global-keyboard backends.
        if sys.platform.startswith("linux"):
            listen_with_evdev(gun_sound, bomb_sound, load_sound)
        else:
            listen_with_pynput(gun_sound, bomb_sound, load_sound)
    except KeyboardInterrupt:
        pass
    except Exception as exc:
        print(f"Keyboard listener error: {exc}", file=sys.stderr)
        return 1
    finally:
        pygame.mixer.stop()
        pygame.mixer.quit()

    print("Stopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
