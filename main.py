#!/usr/bin/env python3
"""Play sound effects in response to global keyboard input."""

from pathlib import Path
import os
import sys

# Keep pygame's startup message out of this command-line program.
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
from pynput import keyboard


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


def main() -> int:
    try:
        gun_sound, bomb_sound, load_sound = load_sounds()
    except (FileNotFoundError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    def on_press(key: keyboard.Key | keyboard.KeyCode) -> bool | None:
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

    print("Listening globally. Press Esc to quit.")
    try:
        with keyboard.Listener(on_press=on_press) as listener:
            listener.join()
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
