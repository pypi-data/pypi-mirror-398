from __future__ import annotations
# from ..Base import *
from ..Proxy import proxy_property, AccessMode
from ..AcadObject import *

class AcadRegisteredApplication(AcadObject):
    def __init__(self, obj) -> None: super().__init__(obj)

    Name: str = proxy_property(str,'Name',AccessMode.ReadWrite)