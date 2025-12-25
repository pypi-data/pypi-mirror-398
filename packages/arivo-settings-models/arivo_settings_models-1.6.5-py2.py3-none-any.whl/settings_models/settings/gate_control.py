from enum import Enum
from typing import Optional

from settings_models._combat import SettingsModel, Field
from settings_models.validators import hhmm_validator


class GateMode(str, Enum):
    """
    How the gate should behave
    """
    automatic = "automatic"
    permanent_open = "permanent_open"
    permanent_close = "permanent_close"
    standard = "standard"


class DayMode(SettingsModel):
    """
    If day mode (everyone can enter) is enabled and at what time of day
    """
    enabled: bool
    start: str = Field("00:00", description="Start of day mode in format HH:MM local time")
    end: str = Field("00:00", description="End of day mode in format HH:MM local time")

    start_validator = hhmm_validator("start")
    end_validator = hhmm_validator("end")


GateModeType = Optional[GateMode]
GateModeType.__doc__ = GateMode.__doc__
DayModeType = Optional[DayMode]
DayModeType.__doc__ = DayMode.__doc__
