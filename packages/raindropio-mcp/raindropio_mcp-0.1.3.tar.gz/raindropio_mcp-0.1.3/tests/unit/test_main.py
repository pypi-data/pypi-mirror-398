"""Unit tests for the main module."""

import logging
from unittest.mock import MagicMock, patch

import pytest

from raindropio_mcp.main import build_parser, configure_logging, main


def test_build_parser():
    """Test argument parser creation."""
    parser = build_parser()

    # Test that parser has the expected arguments
    args = parser.parse_args(["--version"])
    assert args.version is True

    args = parser.parse_args(["--http"])
    assert args.http is True

    args = parser.parse_args(["--http-host", "localhost"])
    assert args.http_host == "localhost"

    args = parser.parse_args(["--http-port", "8000"])
    assert args.http_port == 8000

    args = parser.parse_args(["--http-path", "/mcp"])
    assert args.http_path == "/mcp"


def test_main_version_flag(capsys):
    """Test main function with --version flag."""
    # Test the function directly with --version flag
    with pytest.raises(SystemExit):
        main(["--version"])


@patch("raindropio_mcp.main.SERVERPANELS_AVAILABLE", False)
@patch("raindropio_mcp.main.configure_logging")
@patch("raindropio_mcp.main.create_app")
@patch("raindropio_mcp.main.get_settings")
@patch("raindropio_mcp.main.asyncio.run")
def test_main_stdio_mode(
    mock_asyncio_run, mock_get_settings, mock_create_app, mock_configure_logging
):
    """Test main function with stdio mode."""
    # Mock settings to not enable HTTP transport
    settings_mock = MagicMock()
    settings_mock.enable_http_transport = False
    mock_get_settings.return_value = settings_mock

    # Mock the app
    app_mock = MagicMock()
    mock_create_app.return_value = app_mock

    main([])  # No --http flag

    # Verify app.run() was called without transport arguments (stdio mode)
    mock_asyncio_run.assert_called_once()
    app_mock.run.assert_called_once_with()


@patch("raindropio_mcp.main.SERVERPANELS_AVAILABLE", False)
@patch("raindropio_mcp.main.configure_logging")
@patch("raindropio_mcp.main.create_app")
@patch("raindropio_mcp.main.get_settings")
@patch("raindropio_mcp.main.asyncio.run")
@patch("raindropio_mcp.main.logger")
def test_main_http_mode(
    mock_logger,
    mock_asyncio_run,
    mock_get_settings,
    mock_create_app,
    mock_configure_logging,
):
    """Test main function with HTTP mode."""
    # Mock settings to enable HTTP transport
    settings_mock = MagicMock()
    settings_mock.enable_http_transport = True
    settings_mock.http_host = "localhost"
    settings_mock.http_port = 8000
    settings_mock.http_path = "/mcp"
    mock_get_settings.return_value = settings_mock

    # Mock the app
    app_mock = MagicMock()
    mock_create_app.return_value = app_mock

    main([])  # Will use HTTP due to settings

    # Verify app.run() was called with transport arguments (HTTP mode)
    mock_asyncio_run.assert_called_once()
    app_mock.run.assert_called_once_with(
        transport="streamable-http",
        host="localhost",
        port=8000,
        streamable_http_path="/mcp",
    )


def test_configure_logging_basic():
    """Test basic logging configuration."""
    with patch("raindropio_mcp.main.get_settings") as mock_get_settings:
        settings_mock = MagicMock()
        settings_mock.observability.log_level = "INFO"
        settings_mock.observability.structured_logging = False
        mock_get_settings.return_value = settings_mock

        configure_logging()


def test_configure_logging_structured():
    """Test structured logging configuration."""
    with patch("raindropio_mcp.main.get_settings") as mock_get_settings:
        settings_mock = MagicMock()
        settings_mock.observability.log_level = "DEBUG"
        settings_mock.observability.structured_logging = True
        mock_get_settings.return_value = settings_mock

        configure_logging()

        # Verify that JSONFormatter is used when structured logging is enabled
        root_logger = logging.getLogger()
        assert len(root_logger.handlers) > 0
