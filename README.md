# Keyboard Sounds

A small Python 3 program that listens for keyboard events globally:

- Letters and digits play `assets/gun.mp3`.
- Return/Enter plays `assets/blast.mp3`.
- Backspace or Space plays `assets/load.mp3`.
- Other keys are ignored.
- Escape exits cleanly.

## Install

From this directory, create and activate a virtual environment, then install the
two dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

Copy your audio files into place so the paths are exactly:

```text
assets/gun.mp3
assets/blast.mp3
assets/load.mp3
```

Run the program with:

```bash
python3 main.py
```

## macOS permissions

macOS restricts global keyboard monitoring. Open **System Settings → Privacy &
Security** and grant the application that launches Python (usually Terminal,
iTerm, or your IDE) these permissions:

1. **Accessibility** — allows the process to receive global keyboard events.
2. **Input Monitoring** — allows the process to monitor keyboard input while
   another application is focused.

If the application is not listed, use the `+` button to add it. Quit and reopen
Terminal/iTerm/your IDE after changing either permission, then activate the
virtual environment and run the program again. If you launch it from a different
terminal or IDE later, that application may need its own permissions.

On first use, macOS may display a permission prompt. Approve it in System
Settings; if events still are not received, restart the launching application.

This project uses `pygame-ce`, imported in the code as `pygame`. It provides a
macOS wheel with mixer support for Python 3.14 and Apple Silicon. A native arm64
Python (for example from Homebrew or python.org) is recommended.

If the environment previously had the original `pygame` package installed,
remove it before reinstalling because both packages use the same import name:

```bash
python3 -m pip uninstall -y pygame pygame-ce
python3 -m pip install -r requirements.txt
```
