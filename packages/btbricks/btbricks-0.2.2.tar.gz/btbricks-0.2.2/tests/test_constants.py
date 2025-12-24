"""Tests for btbricks constants."""

import pytest


class TestRCConstants:
    """Test RC control constants."""

    def test_stick_constants(self):
        """Test that stick constants are defined correctly."""
        from btbricks import (
            L_STICK_HOR,
            L_STICK_VER,
            R_STICK_HOR,
            R_STICK_VER,
        )

        assert L_STICK_HOR == 0
        assert L_STICK_VER == 1
        assert R_STICK_HOR == 2
        assert R_STICK_VER == 3

    def test_trigger_constants(self):
        """Test that trigger constants are defined correctly."""
        from btbricks import L_TRIGGER, R_TRIGGER

        assert L_TRIGGER == 4
        assert R_TRIGGER == 5

    def test_button_and_setting_constants(self):
        """Test button and setting constants."""
        from btbricks import BUTTONS, SETTING1, SETTING2

        assert BUTTONS == 8
        assert SETTING1 == 6
        assert SETTING2 == 7

    def test_constants_are_unique(self):
        """Test that all RC constants are unique."""
        from btbricks import (
            L_STICK_HOR,
            L_STICK_VER,
            R_STICK_HOR,
            R_STICK_VER,
            L_TRIGGER,
            R_TRIGGER,
            SETTING1,
            SETTING2,
            BUTTONS,
        )

        constants = [
            L_STICK_HOR,
            L_STICK_VER,
            R_STICK_HOR,
            R_STICK_VER,
            L_TRIGGER,
            R_TRIGGER,
            SETTING1,
            SETTING2,
            BUTTONS,
        ]

        assert len(constants) == len(set(constants))


class TestPortConstants:
    """Test port mapping constants in BtHub."""

    def test_port_mapping(self):
        """Test that BtHub has correct port mapping."""
        from btbricks import BtHub

        with __import__("unittest.mock").mock.patch("btbricks.bthub.BLEHandler"):
            hub = BtHub()
            # Check that _BtHub__PORTS exists (name-mangled private attribute)
            assert hasattr(hub, "_BtHub__PORTS")
