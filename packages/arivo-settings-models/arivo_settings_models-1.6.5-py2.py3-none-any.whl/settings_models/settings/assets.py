from datetime import datetime, UTC
from enum import Enum
from typing import Union, Any

from pydantic import root_validator

from settings_models._combat import SettingsModel, Field
from settings_models.validators import timezone_validator


def utcnow():
    return datetime.now(UTC).replace(tzinfo=None)


class AssetVisualType(str, Enum):
    logo = "logo"
    marketing_image = "marketing_image"  # legacy
    tariff_table = "tariff_table"
    payment_methods = "payment_methods"


class AssetVisualDefinition(SettingsModel):
    """
    Settings for available assets
    """
    type: Union[AssetVisualType, str] = Field(..., description="Type of asset defining its behavior")
    value: Any = Field(description="URL or config of the asset")
    created: datetime = Field(default_factory=utcnow, description="Creation time (UTC) of the asset")

    created_validator = timezone_validator("created")

    @root_validator(pre=False)
    def ensure_created_naive(cls, values):
        if (values["type"] in [AssetVisualType.logo, AssetVisualType.marketing_image]
                and not isinstance(values["value"], str)):
            raise ValueError("Field value must be a string (URL) for logo and marketing_image types")
        return values


AssetVisualDefinitions = dict[str, AssetVisualDefinition]
