from __future__ import annotations
from ..Base import *
from ..Proxy import *
from .AcadSubEntity import *



class AcadSubDMeshEdge(AcadSubEntity):
    def __init__(self, obj) -> None: super().__init__(obj)

    CreaseLevel: float = proxy_property(float,'CreaseLevel',AccessMode.ReadWrite)
    CreaseType: AcMeshCreaseType = proxy_property('AcMeshCreaseType','CreaseType',AccessMode.ReadWrite)