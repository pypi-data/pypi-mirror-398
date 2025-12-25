from enum import Enum
from typing import Optional, Dict, Union

from pydantic import root_validator

from settings_models._combat import SettingsModel, Field


class SignalType(str, Enum):
    permanently_closed = "permanently_closed"
    shortterm_full = "shortterm_full"
    open = "open"
    close_pulse = "close_pulse"
    present_raw = "present_raw"
    present_decision = "present_decision"
    traffic_light_green = "traffic_light_green"
    area_full = "area_full"
    parkinglot_full = "parkinglot_full"
    physical_entry_button = "physical_entry_button"
    custom = "custom"

    @staticmethod
    def gate_related_types():
        return [SignalType.permanently_closed, SignalType.shortterm_full, SignalType.open, SignalType.close_pulse,
                SignalType.present_raw, SignalType.present_decision, SignalType.traffic_light_green]


class SignalDefinition(SettingsModel):
    """
    Settings for available signals
    """
    signal: str = Field(..., description="Technical name of signal")
    name: str = Field(..., description="Human readable name of signal")
    type: Union[SignalType, str] = Field(..., description="Type of signal defining its behavior")
    gate: Optional[str] = Field(None, description="Gate of signal for gate related signals")
    parking_area_id: Optional[str] = Field(None, description="Parking area of signal for gate related signals")

    @root_validator(skip_on_failure=True)
    def data_validation(cls, values):
        if (values["type"] == SignalType.parkinglot_full and
                (values["gate"] is not None or values["parking_area_id"] is not None)):
            raise ValueError("gate and parking_area_id must be None for parkinglot_full signal")
        elif values["type"] == SignalType.parkinglot_full and values["signal"] != "parkinglot_full":
            raise ValueError("only signal parkinglot_full can be of type parkinglot_full")
        elif (values["type"] == SignalType.area_full and
                (values["gate"] is not None or values["parking_area_id"] is None)):
            raise ValueError("parking_area_id must not be None and gate must be None for area_full signal")
        elif (values["type"] in SignalType.gate_related_types() and
                (values["gate"] is None or values["parking_area_id"] is not None)):
            raise ValueError("gate must not be None and parking_area_id must be None for gate related signal")
        return values


class InputType(str, Enum):
    presence_loop = "presence_loop"
    safety_loop = "safety_loop"
    presence_laserscanner = "presence_laserscanner"
    safety_laserscanner = "safety_laserscanner"
    presence_narrow = "presence_narrow"
    safety_narrow = "safety_narrow"
    custom = "custom"


class InputDefinition(SettingsModel):
    """
    Settings for available inputs
    """
    input: str = Field(..., description="Technical name of input")
    name: str = Field(..., description="Human readable name of input")
    type: Union[InputType, str] = Field(..., description="Type of input defining its behavior and usage")
    gate: Optional[str] = Field(None, description="Gate of input for all inputs except custom, where it's optional")
    active: bool = Field(..., description="Whether input is active. False for preconfigured or disabled inputs")

    @root_validator(skip_on_failure=True)
    def data_validation(cls, values):
        if values["type"] != InputType.custom and values["gate"] is None:
            raise ValueError("gate must not be None for inputs except of type custom")
        return values


SignalDefinitions = Dict[str, SignalDefinition]
InputDefinitions = Dict[str, InputDefinition]
