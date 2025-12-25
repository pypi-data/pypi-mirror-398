from __future__ import annotations
from ..Base import *
from ..Proxy import *
from .AcadSurface import AcadSurface



class AcadSweptSurface(AcadSurface):
    def __init__(self, obj) -> None: super().__init__(obj)

    Bank: bool = proxy_property(bool,'Bank',AccessMode.ReadWrite)
    ProfileRotation: float = proxy_property(float,'ProfileRotation',AccessMode.ReadWrite)
    Scale: float = proxy_property(float,'Scale',AccessMode.ReadWrite)
    Twist: float = proxy_property(float,'Twist',AccessMode.ReadWrite)

    def Copy(self) -> AcadSweptSurface:
        return AcadSweptSurface(self._obj.Copy())