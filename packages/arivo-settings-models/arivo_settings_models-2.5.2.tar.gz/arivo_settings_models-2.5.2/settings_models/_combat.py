try:
    from openmodule.models.base import OpenModuleModel as SettingsModel, Field
except ImportError:
    from pydantic import BaseModel as SettingsModel, Field
