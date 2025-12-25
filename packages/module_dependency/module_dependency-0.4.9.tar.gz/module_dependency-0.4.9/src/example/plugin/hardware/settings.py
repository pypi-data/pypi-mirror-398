from pydantic import BaseModel

class HardwarePluginConfig(BaseModel):
    config: bool
