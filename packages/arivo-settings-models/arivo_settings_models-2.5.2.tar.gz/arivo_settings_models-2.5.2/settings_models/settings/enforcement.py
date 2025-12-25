from datetime import datetime
from typing import Optional

from settings_models._combat import SettingsModel, Field
from settings_models.validators import timezone_validator, deprecated_validator


class EnforcementSettings(SettingsModel):
    """
    Settings for enforcement service
    """
    payment_deadline_hours: int = Field(..., gt=0, le=960,
                                        description="How long someone can pay after exiting parking lot "
                                                    "(not including generally applied additional day)")
    strictness: int = Field(default=2, deprecated="The field `EnforcementSettings.strictness` is deprecated "
                                                  "and will be removed in a future version.",
                            description="Strictness level for enforcement. Values to be defined.")
    enabled: bool = Field(..., description="If enforcement is enabled")
    ai_enabled: bool = Field(default=True, description="If the Arivo AI is enabled")
    last_edited: datetime = Field(..., description="Last time (UTC) when enabled setting was changed")

    last_edited_validator = timezone_validator("last_edited")
    strictness_validator = deprecated_validator("strictness")


EnforcementSettingsType = Optional[EnforcementSettings]
EnforcementSettingsType.__doc__ = EnforcementSettings.__doc__
