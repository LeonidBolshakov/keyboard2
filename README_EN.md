# Keyboard2

[Русский](README.md)

**Keyboard2** is a Windows utility for switching keyboard layout with a single key and fixing text typed in the wrong layout.

I built this tool to remove several frustrating keyboard workflows from my daily work:

- switching layout with `Alt+Shift` can trigger side effects in the active application;
- when typing regularly in Russian and English, it is easy to forget the current layout, type a phrase with the wrong characters, and then find that the active application does not make it possible to fix the text without typing it again;
- the same personal snippets often need to be entered again and again: e-mail, phone number, signature, or short text templates.

## Screenshot

![Selected text replacement dialog](docs/images/keyboard2-dialog.png)

## Demo

[Watch a short demo](docs/images/keyboard2-demo.mp4)

[Watch a short demo](docs/images/keyboard2-demo.mp4)

## Features

- Switches keyboard layout with one key: `Caps Lock`.
- Fixes selected text typed in the wrong layout: `Scroll Lock`.
- Shows a confirmation dialog with the original and replacement text.
- Supports `--fast` mode, where replacement is applied without a confirmation dialog.
- Inserts configured personal snippets with global hotkeys.
- Runs from the system tray.
- Launches a selected external program, for example a custom calculator.
- Prevents a second application instance from starting.
- Provides logging and can be packaged as a standalone `.exe` with PyInstaller.

## Hotkeys

- `Caps Lock` - switch keyboard layout.
- `Scroll Lock` - fix selected text typed in the wrong layout.
- `Ctrl+F3` - insert e-mail from settings.
- `Ctrl+F4` - insert phone number from settings.
- `Ctrl+F5` - launch a selected external program, for example a custom calculator.
- `Ctrl+F9` - insert signature from settings.

## Example

The user wanted to type:

```text
привет
```

But the text was entered with the English layout enabled:

```text
ghbdsn
```

Select the incorrect text and press `Scroll Lock`. Keyboard2 reads the selection through the clipboard, converts characters according to the Russian and English keyboard layout mapping, and suggests replacing the text.

In `--fast` mode, the confirmation dialog is skipped and the selected text is replaced immediately.

## Settings

The application reads user values from `.env` through `python-dotenv`.

Example `.env`:

```env
EMAIL=user@example.com
TELEPHONE="+7 000 000-00-00"
SIGNATURE="Best regards,\nFirst Last"
CALCULATOR=C:\Windows\System32\calc.exe
CONSOLE_LOG_LEVEL=INFO
FILE_LOG_LEVEL_INFO=DEBUG
FILE_LOG_PATH=C:\Temp\keyboard2.log
```

The real `.env` file should not be committed to the repository. The project includes `.env.example` as a public example.

## Run From Source

The project is intended for Windows. Runtime dependencies are kept in `requirements.txt`.

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python .\src\keyboard2.py
```

Fast mode:

```powershell
python .\src\keyboard2.py --fast
```

## Build EXE

Development and build tools are kept in `requirements-dev.txt`. The project includes `keyboard2.spec` for PyInstaller builds.

```powershell
pip install -r requirements-dev.txt
pyinstaller keyboard2.spec
```

The executable will be created in the `dist` directory.

## Checks

Install development dependencies before running tests and checks:

```powershell
pip install -r requirements-dev.txt
```

Run tests:

```powershell
pytest
```

Check formatting and types:

```powershell
black --check src tests
mypy
```

## Architecture

The project is split into focused modules:

- `src/keyboard2.py` - application entry point, logging setup, and top-level exception handling.
- `src/app.py` - PyQt6 application lifecycle, system tray, hotkey registration, and single-instance guard.
- `src/main_window.py` - text replacement dialog and user interaction.
- `src/controller.py` - coordination layer between UI and hotkey handlers.
- `src/hotkeys_handlers.py` - actions executed by hotkeys.
- `src/replacetext.py` - text conversion between Russian and English keyboard layouts.
- `src/windows_hotkeys.py` - global hotkey registration through WinAPI.
- `src/ll_keyboard.py` - low-level keyboard hook for special keys.
- `src/send_input_keys.py` - keyboard and text input through WinAPI `SendInput`.
- `src/win_clipboard.py` - Windows clipboard integration.
- `src/single_instance.py` - duplicate launch protection.
- `src/tune_logger.py` - logging configuration.

## Technical Details

The project uses:

- Python;
- PyQt6;
- WinAPI;
- global hotkeys;
- low-level keyboard hook;
- clipboard integration;
- `SendInput` for programmatic input;
- `python-dotenv` for settings;
- `logging` with a file log;
- PyInstaller for `.exe` packaging.

## Limitations

- The application is Windows-only.
- Some features may require administrator privileges.
- Global hotkeys depend on the Windows environment and already occupied key combinations.
- Working with selected text depends on the behavior of the active application.

## Project Status

This project is being prepared for a portfolio publication. Planned improvements:

- configure GitHub Actions for project checks.
