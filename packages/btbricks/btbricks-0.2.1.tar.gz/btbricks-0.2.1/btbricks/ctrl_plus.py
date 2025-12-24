from .bthub import BtHub

# Backward compatibility
class SmartHub(BtHub):
    """
    This class is kept for backward compatibility. Use :class:`BtHub` instead.
    """
    pass