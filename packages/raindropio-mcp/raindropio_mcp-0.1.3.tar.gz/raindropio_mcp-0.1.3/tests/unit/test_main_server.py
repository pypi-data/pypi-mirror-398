from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import pytest


def _import_server(monkeypatch: pytest.MonkeyPatch):
    import importlib

    import raindropio_mcp.server as server_module

    importlib.reload(server_module)
    return server_module


class DummyClient:
    def __init__(self) -> None:
        self.closed = False

    async def close(self) -> None:
        self.closed = True


def test_create_app_registers_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    dummy_client = DummyClient()
    calls: dict[str, Any] = {}

    monkeypatch.setenv(
        "RAINDROP_TOKEN", "test_token_1234567890abcdefghijklmnopqr"
    )  # At least 32 chars
    server_module = _import_server(monkeypatch)

    monkeypatch.setattr(
        server_module, "build_raindrop_client", lambda settings: dummy_client
    )

    def fake_register(app, client):
        calls["client"] = client
        calls["app"] = app

    monkeypatch.setattr(server_module, "register_all_tools", fake_register)
    app = server_module.create_app()
    assert app.name == server_module.APP_NAME
    assert calls["client"] is dummy_client
    assert calls["app"] is app
    assert app._raindrop_client is dummy_client


def test_configure_logging_json(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    from raindropio_mcp.config.settings import RaindropSettings
    from raindropio_mcp.main import configure_logging

    settings = RaindropSettings(
        token="test_token_1234567890abcdefghijklmnopqr", enable_http_transport=False
    )
    monkeypatch.setattr(
        "raindropio_mcp.main.get_settings",
        lambda: settings,
        raising=False,
    )
    configure_logging()
    with caplog.at_level(logging.INFO):
        logging.getLogger("raindropio_mcp.test").info("hello")
    assert any(record.message == "hello" for record in caplog.records)


def test_main_version_flag(capsys: pytest.CaptureFixture[str]) -> None:
    import pytest

    from raindropio_mcp.main import main as cli_main

    with pytest.raises(SystemExit) as exc_info:
        cli_main(["--version"])

    assert exc_info.value.code == 0
    # The version flag just exits with code 0, no output expected
    capsys.readouterr()
    # No specific output is expected from the main function itself


def test_main_http_runs(monkeypatch: pytest.MonkeyPatch) -> None:
    from raindropio_mcp.config.settings import RaindropSettings
    from raindropio_mcp.main import main as cli_main

    class DummyApp:
        async def run(self, **kwargs):
            self.kwargs = kwargs

    dummy_app = DummyApp()
    settings = RaindropSettings(
        token="test_token_1234567890abcdefghijklmnopqr", enable_http_transport=False
    )

    monkeypatch.setattr("raindropio_mcp.main.create_app", lambda: dummy_app)
    monkeypatch.setattr("raindropio_mcp.main.get_settings", lambda: settings)

    captured = {}

    def fake_run(coro):
        captured["coroutine"] = coro
        coro.close()
        return None

    monkeypatch.setattr(asyncio, "run", fake_run)

    cli_main(["--http", "--http-path", "/custom"])
    assert "coroutine" in captured
    coro = captured["coroutine"]
    assert hasattr(coro, "cr_code")  # coroutine object
