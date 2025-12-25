from __future__ import annotations
from ..Base import *
from ..Proxy import *
from .AcadSubEntity import *

class AcadSubEntSolidFace(AcadSubEntity):
    def __init__(self, obj) -> None: super().__init__(obj)
    
    Material: str = proxy_property(str,'Material',AccessMode.ReadWrite)