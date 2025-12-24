from enum import Enum


class DeviceType(Enum):
    Ups = "ups"
    Pdu = "pdu"
    Scd = "scd"
    Psu = "psu"
    Ats = "ats"


class UpsStatus(Enum):
    """https://networkupstools.org/docs/developer-guide.chunked/new-drivers.html#status-data"""

    Online = "OL"
    OnBattery = "OB"
    LowBattery = "LB"
    HighBattery = "HB"
    ReplaceBattery = "RB"
    Charging = "CHRG"
    Discharging = "DISCHRG"
    Bypass = "BYPASS"
    Calibrating = "CAL"
    Off = "OFF"
    Overloaded = "OVER"
    Trimming = "TRIM"
    Boosting = "BOOST"
    ForcedShutdown = "FSD"


class BeeperStatus(Enum):
    Enabled = "enabled"
    Disabled = "disabled"
    Muted = "muted"


class UpsMode(Enum):
    """https://networkupstools.org/docs/developer-guide.chunked/_variables.html#note-3"""

    Online = "online"
    LineInteractive = "line-interactive"
    Bypass = "bypass"
