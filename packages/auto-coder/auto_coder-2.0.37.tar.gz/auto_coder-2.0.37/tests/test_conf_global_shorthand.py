import os
from pathlib import Path
import json
import pytest

from autocoder.chat.conf_command import handle_conf_command
from autocoder.common.core_config import (
    get_memory_manager,
    get_global_memory_manager,
)
import autocoder.common.core_config.main_manager as main_manager_mod


def test_project_shorthand_sets_value(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    # Use an isolated project root
    project_root = tmp_path / "proj"
    project_root.mkdir(parents=True, exist_ok=True)
    monkeypatch.chdir(project_root)

    # Set via shorthand
    msg = handle_conf_command("project_key:123")
    assert "project_key" in msg

    # Verify via manager (project scope)
    mm = get_memory_manager(str(project_root))
    assert mm.get_config("project_key", source="project") == 123


def test_global_shorthand_sets_value(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    # Prepare isolated fake HOME: ~/.auto-coder/plugins/chat-auto-coder
    fake_home = tmp_path / "home"
    global_conf_dir = fake_home / ".auto-coder" / "plugins" / "chat-auto-coder"
    global_conf_dir.mkdir(parents=True, exist_ok=True)

    # Monkeypatch the global config dir resolver used by get_global_memory_manager
    monkeypatch.setattr(
        main_manager_mod,
        "get_global_config_dir",
        lambda: global_conf_dir,
        raising=True,
    )

    # Use global shorthand to set value
    msg = handle_conf_command("/global metaso_api_key:xxxx")
    assert "metaso_api_key" in msg
    assert "(global)" in msg  # scope suffix present

    # Verify value persisted in the global manager's project scope
    gmm = get_global_memory_manager()
    assert gmm.get_config("metaso_api_key", source="project") == "xxxx"
