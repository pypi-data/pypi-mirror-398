from __future__ import annotations
from ..Base import *
from ..Proxy import *
from ..AcadEntity import AcadEntity



class Acad3DPolyline(AcadEntity):
    def __init__(self, obj) -> None: super().__init__(obj)

    Closed: bool = proxy_property(bool,'Closed',AccessMode.ReadWrite)
    Coordinates: PyGePoint3dArray = proxy_property('PyGePoint3dArray','Coordinates',AccessMode.ReadWrite)
    Length: float = proxy_property(float,'Length',AccessMode.ReadOnly)
    Type: Ac3DPolylineType = proxy_property('Ac3DPolylineType','Type',AccessMode.ReadWrite)

    def Coordinate(self, Index: int) -> PyGePoint3d:
        return PyGePoint3d(self._obj.Coordinate(Index))
        
    def Copy(self) -> Acad3DPolyline:
        return Acad3DPolyline(self._obj.Copy())
        
    def AppendVertex(self, Point: PyGePoint3d) -> None:
        self._obj.AppendVertex(Point())
        
    def Explode(self) -> vObjectArray:
        return vObjectArray(self._obj.Explode())