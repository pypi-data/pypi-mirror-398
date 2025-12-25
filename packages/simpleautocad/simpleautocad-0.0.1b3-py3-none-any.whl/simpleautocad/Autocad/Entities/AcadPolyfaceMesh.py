from __future__ import annotations
from ..Base import *
from ..Proxy import *
from ..AcadEntity import AcadEntity



class AcadPolyfaceMesh(AcadEntity):
    def __init__(self, obj) -> None: super().__init__(obj)

    Coordinates: PyGePoint3dArray = proxy_property('PyGePoint3dArray','Coordinates',AccessMode.ReadWrite)
    NumberOfFaces: int = proxy_property(int,'NumberOfFaces',AccessMode.ReadOnly)
    NumberOfVertices: int = proxy_property(int,'NumberOfVertices',AccessMode.ReadOnly)

    def Coordinate(self, Index: int) -> PyGePoint3d:
        return PyGePoint3d(self._obj.Coordinate(Index))

    def Copy(self) -> AcadPolyfaceMesh:
        return AcadPolyfaceMesh(self._obj.Copy())
