"""Tests for BtHub class."""

import pytest
from unittest.mock import Mock, MagicMock, patch


class TestBtHubInitialization:
    """Test BtHub initialization."""

    def test_bthub_init_default(self):
        """Test BtHub initialization with default BLEHandler."""
        from btbricks import BtHub

        with patch("btbricks.bthub.BLEHandler"):
            hub = BtHub()
            assert hub._conn_handle is None
            assert hub.acc_sub is False
            assert hub.gyro_sub is False
            assert hub.tilt_sub is False
            assert isinstance(hub.hub_data, dict)
            assert isinstance(hub.mode_info, dict)

    def test_bthub_init_with_ble_handler(self):
        """Test BtHub initialization with custom BLEHandler."""
        from btbricks import BtHub

        mock_ble = Mock()
        hub = BtHub(ble_handler=mock_ble)
        assert hub.ble_handler is mock_ble
        assert hub._conn_handle is None

    def test_bthub_is_connected_false(self):
        """Test is_connected returns False when not connected."""
        from btbricks import BtHub

        with patch("btbricks.bthub.BLEHandler"):
            hub = BtHub()
            assert hub.is_connected() is False

    def test_bthub_is_connected_true(self):
        """Test is_connected returns True when connected."""
        from btbricks import BtHub

        with patch("btbricks.bthub.BLEHandler"):
            hub = BtHub()
            hub._conn_handle = 1
            assert hub.is_connected() is True


class TestBtHubColorConstants:
    """Test BtHub LED color constants."""

    def test_color_constants_exist(self):
        """Test that color constants are defined."""
        from btbricks.bthub import OFF, PINK, PURPLE, DARK_BLUE, BLUE, TEAL
        from btbricks.bthub import GREEN, YELLOW, ORANGE, RED, WHITE

        colors = [OFF, PINK, PURPLE, DARK_BLUE, BLUE, TEAL, GREEN, YELLOW, ORANGE, RED, WHITE]

        # All should be integers
        assert all(isinstance(c, int) for c in colors)

        # All should be non-negative
        assert all(c >= 0 for c in colors)


class TestBtHubClampInt:
    """Test clamp_int helper function."""

    def test_clamp_int_within_range(self):
        """Test clamp_int with value within range."""
        from btbricks.bthub import clamp_int

        assert clamp_int(50) == 50
        assert clamp_int(0) == 0

    def test_clamp_int_below_min(self):
        """Test clamp_int with value below minimum."""
        from btbricks.bthub import clamp_int

        assert clamp_int(-150) == -100

    def test_clamp_int_above_max(self):
        """Test clamp_int with value above maximum."""
        from btbricks.bthub import clamp_int

        assert clamp_int(150) == 100

    def test_clamp_int_custom_range(self):
        """Test clamp_int with custom floor and ceiling."""
        from btbricks.bthub import clamp_int

        assert clamp_int(5, floor=0, ceiling=10) == 5
        assert clamp_int(-5, floor=0, ceiling=10) == 0
        assert clamp_int(15, floor=0, ceiling=10) == 10

    def test_clamp_int_rounds(self):
        """Test clamp_int rounds values."""
        from btbricks.bthub import clamp_int

        assert clamp_int(50.4) == 50
        assert clamp_int(50.5) == 50 or clamp_int(50.5) == 51  # Banker's rounding
