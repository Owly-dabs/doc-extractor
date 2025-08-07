from pydantic import BaseModel

class Symbol(BaseModel):
    name: str
    parent: str | None = None
    type: str  # "function", "class", etc.

class Docstring(BaseModel):
    file: str | None = None
    name: str
    parent: str | None = None
    type: str
    docstring: str