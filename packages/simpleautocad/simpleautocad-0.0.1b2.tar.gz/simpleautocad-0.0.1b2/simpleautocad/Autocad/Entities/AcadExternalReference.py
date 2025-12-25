from __future__ import annotations
from ..Base import *
from ..Proxy import *
from .AcadBlockReference import AcadBlockReference



class AcadExternalReference(AcadBlockReference):
    def __init__(self, obj) -> None: super().__init__(obj)

    LayerPropertyOverrides: bool = proxy_property(bool,'LayerPropertyOverrides',AccessMode.ReadOnly)
    Path: str = proxy_property(str,'Path',AccessMode.ReadWrite)

    def Copy(self) -> AcadExternalReference:
        return AcadExternalReference(self._obj.Copy())