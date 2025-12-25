from pydantic import BaseModel

class BasePluginConfig(BaseModel):
    config: bool = True
