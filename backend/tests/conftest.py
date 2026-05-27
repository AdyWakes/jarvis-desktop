from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _isolated_db(monkeypatch: pytest.MonkeyPatch):
    """Give every test a fresh sqlite file and reset module-level singletons."""
    tmp = Path(tempfile.mkdtemp())
    db_path = tmp / "jarvis-test.db"
    monkeypatch.setenv("JARVIS_DB_PATH", str(db_path))
    monkeypatch.setenv("OPENAI_API_KEY", os.environ.get("OPENAI_API_KEY", ""))

    import app.config as config_module
    import app.core.memory as memory_module
    import app.services.openai_client as openai_module

    config_module.get_settings.cache_clear()
    openai_module.get_openai_client.cache_clear()
    memory_module._engine = None
    memory_module._session_factory = None

    yield
