from __future__ import annotations
from ..Base import *
from ..Proxy import *
from ..AcadEntity import AcadEntity



class AcadPolygonMesh(AcadEntity):
    def __init__(self, obj) -> None: super().__init__(obj)

    Coordinates: PyGePoint3dArray = proxy_property('PyGePoint3dArray','Coordinates',AccessMode.ReadWrite)
    MClose: bool = proxy_property(bool,'MClose',AccessMode.ReadWrite)
    MDensity: int = proxy_property(int,'MDensity',AccessMode.ReadWrite)
    MVertexCount: int = proxy_property(int,'MVertexCount',AccessMode.ReadOnly)
    NClose: bool = proxy_property(bool,'NClose',AccessMode.ReadWrite)
    NDensity: int = proxy_property(int,'NDensity',AccessMode.ReadWrite)
    NVertexCount: int = proxy_property(int,'NVertexCount',AccessMode.ReadOnly)
    Type: AcPolymeshType   = proxy_property('AcPolymeshType','Type',AccessMode.ReadWrite)


    def Coordinate(self, Index: int) -> PyGePoint3d:
        return PyGePoint3d(self._obj.Coordinate(Index))
        
    def Copy(self) -> AcadPolygonMesh:
        return AcadPolygonMesh(self._obj.Copy())
        
    def AppendVertex(self, Point: PyGePoint3d) -> None:
        self._obj.AppendVertex(Point())
        
    def Explode(self) -> vObjectArray:
        return vObjectArray(self._obj.Explode())
