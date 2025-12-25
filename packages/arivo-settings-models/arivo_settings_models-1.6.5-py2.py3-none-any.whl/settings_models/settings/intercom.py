from typing import Optional

from pydantic import root_validator

from settings_models._combat import SettingsModel, Field


class IntercomSettings(SettingsModel):
    """
    Settings for intercom on kiosk devices
    """
    enabled: bool = Field(..., description="If intercom enabled on kiosk devices")
    phone_number: Optional[str] = Field(None, description="Phone number for intercom emergency calls")

    @root_validator(skip_on_failure=True)
    def data_validation(cls, values):
        if values.get("enabled") and values.get("phone_number") is None:
            raise ValueError("phone_number must be set if intercom is enabled")
        return values
