from pydantic import BaseModel

class Module(BaseModel):
    path: str
    name: str

class Component(BaseModel):
    path: str
    name: str
    interface: str

class Instance(BaseModel):
    path: str
    name: str
    imports: list[str]
