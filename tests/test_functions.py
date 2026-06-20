import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any, cast

fake_pygetwindow = ModuleType("pygetwindow")
cast(Any, fake_pygetwindow)._pygetwindow_win = SimpleNamespace(Win32Window=object)
cast(Any, fake_pygetwindow).getActiveWindow = lambda: None

fake_keyboard = ModuleType("keyboard")
cast(Any, fake_keyboard).send = lambda *args, **kwargs: None
cast(Any, fake_keyboard).release = lambda *args, **kwargs: None
cast(Any, fake_keyboard).write = lambda *args, **kwargs: None

sys.modules.setdefault("pygetwindow", fake_pygetwindow)
sys.modules.setdefault("keyboard", fake_keyboard)

import src.functions as functions


def test_get_exe_directory_returns_project_root_for_source_run(monkeypatch) -> None:
    monkeypatch.delattr(functions.sys, "frozen", raising=False)

    assert (
        functions.get_exe_directory()
        == Path(functions.__file__).resolve().parent.parent
    )


def test_get_exe_directory_returns_meipass_for_pyinstaller_one_file(
    monkeypatch, tmp_path
) -> None:
    bundle_dir = tmp_path / "bundle"
    monkeypatch.setattr(functions.sys, "frozen", True, raising=False)
    monkeypatch.setattr(functions.sys, "_MEIPASS", str(bundle_dir), raising=False)

    assert functions.get_exe_directory() == bundle_dir


def test_get_exe_directory_returns_executable_parent_for_pyinstaller_one_dir(
    monkeypatch, tmp_path
) -> None:
    dist_dir = tmp_path / "dist"
    monkeypatch.setattr(functions.sys, "frozen", True, raising=False)
    monkeypatch.delattr(functions.sys, "_MEIPASS", raising=False)
    monkeypatch.setattr(functions.sys, "executable", str(dist_dir / "keyboard2.exe"))

    assert functions.get_exe_directory() == dist_dir
