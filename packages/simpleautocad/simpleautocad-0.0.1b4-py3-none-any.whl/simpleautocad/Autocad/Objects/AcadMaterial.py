from __future__ import annotations
from ..Base import *
from ..Proxy import *
from ..AcadObject import *


class AcadMaterial(AcadObject):
    def __init__(self, obj) -> None: super().__init__(obj)

    Description: str = proxy_property(str,'Description',AccessMode.ReadWrite)
    Name: str = proxy_property(str,'Name',AccessMode.ReadWrite)
