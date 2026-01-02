# tests/test_banner.py

import os
from unittest.mock import MagicMock, patch

from relm import banner


def test_lerp():
    """
    Tests the linear interpolation function.
    """
    assert banner.lerp(0, 10, 0.5) == 5
    assert banner.lerp(10, 20, 0.25) == 12.5
    assert banner.lerp(5, 5, 0.5) == 5


def test_blend():
    """
    Tests the color blending function.
    """
    c1 = (0, 0, 0)
    c2 = (255, 255, 255)
    assert banner.blend(c1, c2, 0) == "#000000"
    # The blend function is not linear, so 1.0 is not pure white
    assert banner.blend(c1, c2, 1) == "#cfcfcf"
    assert banner.blend(c1, c2, 0.5) == "#5e5e5e"


@patch("rich.console.Console")
def test_print_logo_fixed_palette(mock_console):
    """
    Tests the print_logo function with a fixed palette.
    """
    with patch.dict(os.environ, {"CREATE_DUMP_PALETTE": "0"}):
        banner.print_logo()
        # Assert that the console's print method was called
        mock_console.return_value.print.assert_called()


@patch("rich.console.Console")
def test_print_logo_bad_palette_env(mock_console):
    """
    Tests the print_logo function with a bad palette environment variable.
    """
    with patch.dict(os.environ, {"CREATE_DUMP_PALETTE": "invalid"}):
        banner.print_logo()
        mock_console.return_value.print.assert_called()


@patch("rich.console.Console")
@patch("random.SystemRandom")
def test_print_logo_procedural_palette(mock_system_random, mock_console):
    """
    Tests the print_logo function with a procedural palette.
    """
    # Configure the mock for SystemRandom
    mock_system_random.return_value.random.side_effect = [
        0.5, 0.5, 0.5, 0.5, 0.5,  # base_h and jitter values
        0.5, 0.5, 0.5, 0.5, 0.5,
        0.5, 0.5, 0.5, 0.5, 0.5,
        0.5, 0.5, 0.5, 0.5, 0.5,
        0.1,  # For the occasional bias
    ]
    mock_system_random.return_value.shuffle.return_value = None

    if "CREATE_DUMP_PALETTE" in os.environ:
        del os.environ["CREATE_DUMP_PALETTE"]

    banner.print_logo()
    mock_console.return_value.print.assert_called()
