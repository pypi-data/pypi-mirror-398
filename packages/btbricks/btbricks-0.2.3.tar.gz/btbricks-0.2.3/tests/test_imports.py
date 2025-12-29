"""Test that all public APIs can be imported."""

import pytest


def test_import_btbricks():
    """Test basic import of btbricks package."""
    import btbricks

    assert btbricks.__version__ == "0.1.0"
    assert btbricks.__author__ == "Anton Vanhoucke"


def test_import_bt_module():
    """Test import of bt module classes."""
    from btbricks import (
        BLEHandler,
        UARTCentral,
        UARTPeripheral,
        RCReceiver,
        RCTransmitter,
        MidiController,
    )

    # Just check that classes exist
    assert BLEHandler is not None
    assert UARTCentral is not None
    assert UARTPeripheral is not None
    assert RCReceiver is not None
    assert RCTransmitter is not None
    assert MidiController is not None


def test_import_bthub():
    """Test import of BtHub class."""
    from btbricks import BtHub

    assert BtHub is not None


def test_import_control_constants():
    """Test import of control constants."""
    from btbricks import (
        R_STICK_HOR,
        R_STICK_VER,
        L_STICK_HOR,
        L_STICK_VER,
        BUTTONS,
        L_TRIGGER,
        R_TRIGGER,
        SETTING1,
        SETTING2,
    )

    # Check that constants are defined
    assert isinstance(R_STICK_HOR, int)
    assert isinstance(R_STICK_VER, int)
    assert isinstance(L_STICK_HOR, int)
    assert isinstance(L_STICK_VER, int)
    assert isinstance(BUTTONS, int)
    assert isinstance(L_TRIGGER, int)
    assert isinstance(R_TRIGGER, int)
    assert isinstance(SETTING1, int)
    assert isinstance(SETTING2, int)


def test_control_constants_unique():
    """Test that control constants have unique values."""
    from btbricks import (
        R_STICK_HOR,
        R_STICK_VER,
        L_STICK_HOR,
        L_STICK_VER,
        BUTTONS,
        L_TRIGGER,
        R_TRIGGER,
        SETTING1,
        SETTING2,
    )

    constants = [
        R_STICK_HOR,
        R_STICK_VER,
        L_STICK_HOR,
        L_STICK_VER,
        BUTTONS,
        L_TRIGGER,
        R_TRIGGER,
        SETTING1,
        SETTING2,
    ]

    # All constants should be unique
    assert len(constants) == len(set(constants))
