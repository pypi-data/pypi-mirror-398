from .client import SimpleWizDevice
from .discovery import SimpleWizScanner

class WizScene:
    OCEAN = 1
    ROMANCE = 2
    SUNSET = 3
    PARTY = 4
    FIREPLACE = 5
    COZY = 6
    FOREST = 9
    PASTEL = 10
    WAKE_UP = 11
    BEDTIME = 13
    WARM_WHITE = 32
    DAYLIGHT = 33
    COOL_WHITE = 34

start_push_listener = SimpleWizDevice.start_push_listener

__all__ = ["SimpleWizDevice", "SimpleWizScanner", "start_push_listener", "WizScene"]
__version__ = "0.1.0"
