from pydantic import BaseModel

class ReporterPluginConfig(BaseModel):
    config: bool
