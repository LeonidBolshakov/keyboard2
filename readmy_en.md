# Keyboard2

[Русский](readmy.md)

**Keyboard2** is a Windows utility for switching keyboard layout with a single key and fixing text typed in the wrong layout.

I built this tool to remove several frustrating keyboard workflows from my daily work:

- switching layout with `Alt+Shift` can trigger side effects in the active application;
- when typing regularly in Russian and English, it is easy to forget the current layout, type a phrase with the wrong characters, and then find that the active application does not make it possible to fix the text without typing it again;
- the same personal snippets often need to be entered again and again: e-mail, phone number, signature, or short text templates.

## Screenshot

![Selected text replacement dialog](docs/images/keyboard2-dialog.png)

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

| Hotkey | Action |
| --- | --- |
| `Caps Lock` | Switch keyboard layout |
| `Scroll Lock` | Fix selected text typed in the wrong layout |
| `Ctrl+F3` | Insert e-mail from settings |
| `Ctrl+F4` | Insert phone number from settings |
| `Ctrl+F5` | Launch a selected external program, for example a custom calculator |
| `Ctrl+F9` | Insert signature from settings |

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
e-mail=user@example.com
telephone=+7 000 000-00-00
signature=Best regards,
First Last
calculator=C:\Windows\System32\calc.exe
console_log_level=INFO
file_log_level_info=DEBUG
```

The real `.env` file should not be committed to the repository. Use `.env.example` for public examples.

## Run From Source

The project is intended for Windows.

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python .\SRC\keyboard2.py
```

Fast mode:

```powershell
python .\SRC\keyboard2.py --fast
```

## Build EXE

The project includes `keyboard2.spec` for PyInstaller builds.

```powershell
pyinstaller keyboard2.spec
```

The executable will be created in the `dist` directory.

## Architecture

The project is split into focused modules:

- `SRC/keyboard2.py` - application entry point, logging setup, and top-level exception handling.
- `SRC/app.py` - PyQt6 application lifecycle, system tray, hotkey registration, and single-instance guard.
- `SRC/main_window.py` - text replacement dialog and user interaction.
- `SRC/controller.py` - coordination layer between UI and hotkey handlers.
- `SRC/hotkeys_handlers.py` - actions executed by hotkeys.
- `SRC/replacetext.py` - text conversion between Russian and English keyboard layouts.
- `SRC/windows_hotkeys.py` - global hotkey registration through WinAPI.
- `SRC/ll_keyboard.py` - low-level keyboard hook for special keys.
- `SRC/send_input_keys.py` - keyboard and text input through WinAPI `SendInput`.
- `SRC/win_clipboard.py` - Windows clipboard integration.
- `SRC/single_instance.py` - duplicate launch protection.
- `SRC/tune_logger.py` - logging configuration.

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

- add `.env.example`;
- split runtime and development dependencies;
- add tests for text replacement logic;
- add `pyproject.toml` with formatting and type-checking settings;
- configure GitHub Actions for project checks.