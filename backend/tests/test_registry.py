from __future__ import annotations

from app.config import Settings
from app.core.registry import build_default_registry


def test_registry_includes_core_tools() -> None:
    settings = Settings(
        OPENAI_API_KEY="sk-test",  # type: ignore[call-arg]
    )
    registry = build_default_registry(settings)
    names = {t.name for t in registry.all()}
    assert {
        "open_application",
        "browse_web",
        "summarize_file",
        "add_task",
        "list_tasks",
        "complete_task",
        "delete_task",
        "system_info",
    }.issubset(names)


def test_registry_respects_toggles() -> None:
    settings = Settings(
        OPENAI_API_KEY="sk-test",  # type: ignore[call-arg]
        JARVIS_ENABLE_APP_LAUNCHER=False,
        JARVIS_ENABLE_BROWSER=False,
        JARVIS_ENABLE_FILE_SUMMARIZER=False,
        JARVIS_ENABLE_TASK_MEMORY=False,
    )
    registry = build_default_registry(settings)
    names = {t.name for t in registry.all()}
    assert names == {"system_info"}


def test_openai_schemas_have_function_payload() -> None:
    settings = Settings(OPENAI_API_KEY="sk-test")  # type: ignore[call-arg]
    registry = build_default_registry(settings)
    for schema in registry.openai_schemas():
        assert schema["type"] == "function"
        assert "name" in schema["function"]
        assert "parameters" in schema["function"]
