from __future__ import annotations
from ..Base import *
from ..Proxy import *
from .AcadSubEntity import *



class AcadSubDMeshVertex(AcadSubEntity):
    def __init__(self, obj) -> None: super().__init__(obj)

    Coordinates: PyGePoint3dArray = proxy_property('PyGePoint3dArray','Coordinates',AccessMode.ReadWrite)
    CreaseLevel: float = proxy_property(float,'CreaseLevel',AccessMode.ReadWrite)
    CreaseType: AcMeshCreaseType = proxy_property('AcMeshCreaseType','CreaseType',AccessMode.ReadWrite)