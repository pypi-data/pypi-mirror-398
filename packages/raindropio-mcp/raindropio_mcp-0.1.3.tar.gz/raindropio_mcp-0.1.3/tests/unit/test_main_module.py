"""Unit tests for the __main__ module entrypoint."""

import pytest

from raindropio_mcp.main import main


def test_main_module_entrypoint():
    """Test that calling main with version arg works correctly."""
    with pytest.raises(SystemExit):
        main(["--version"])
