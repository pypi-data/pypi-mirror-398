from __future__ import annotations
from ..Base import *
from ..Proxy import *
from .AcadSurface import AcadSurface



class AcadNurbSurface(AcadSurface):
    def __init__(self, obj) -> None: super().__init__(obj)

    CvHullDisplay: bool = proxy_property(bool,'CvHullDisplay',AccessMode.ReadWrite)
    Height: float = proxy_property(float,'Height',AccessMode.ReadWrite)

    def Copy(self) -> AcadNurbSurface:
        return AcadNurbSurface(self._obj.Copy())