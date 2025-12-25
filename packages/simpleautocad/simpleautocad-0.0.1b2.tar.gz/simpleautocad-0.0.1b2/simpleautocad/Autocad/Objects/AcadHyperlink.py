from __future__ import annotations
from ..Base import *
from ..Proxy import proxy_property, AccessMode
from ..AcadObject import *

class AcadHyperlink(AppObject):
    def __init__(self, obj) -> None: super().__init__(obj)

    Application: AcadApplication = proxy_property('AcadApplication','Application',AccessMode.ReadOnly)
    URL: str = proxy_property(str,'URL',AccessMode.ReadWrite)
    URLDescription: str = proxy_property(str,'URLDescription',AccessMode.ReadWrite)
    URLNamedLocation: str = proxy_property(str,'URLNamedLocation',AccessMode.ReadWrite)

    def Delete(self) -> None: 
        self._obj.Delete()