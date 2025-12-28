from __future__ import annotations
from ..Base import *
from ..Proxy import *
from ..AcadEntity import AcadEntity



class AcadPolyline(AcadEntity):
    def __init__(self, obj) -> None: super().__init__(obj)

    Area: float = proxy_property(float,'Area',AccessMode.ReadOnly)
    Closed: bool = proxy_property(bool,'Closed',AccessMode.ReadWrite)
    ConstantWidth: float = proxy_property(float,'ConstantWidth',AccessMode.ReadWrite)
    Coordinates: PyGePoint3dArray = proxy_property('PyGePoint3dArray','Coordinates',AccessMode.ReadWrite)
    Elevation: float = proxy_property(float,'Elevation',AccessMode.ReadWrite)
    Length: float = proxy_property(float,'Length',AccessMode.ReadOnly)
    LinetypeGeneration: bool = proxy_property(bool,'LinetypeGeneration',AccessMode.ReadWrite)
    Normal: PyGeVector3d = proxy_property('PyGeVector3d','Normal',AccessMode.ReadWrite)
    Thickness: float = proxy_property(float,'Thickness',AccessMode.ReadWrite)
    Type: AcPolylineType = proxy_property('AcPolylineType','Type',AccessMode.ReadWrite)

    def Coordinate(self, Index: int) -> PyGePoint3d:
        return PyGePoint3d(self._obj.Coordinate(Index))

    def Copy(self) -> AcadPolyline:
        return AcadPolyline(self._obj.Copy())

    def AppendVertex(self, Point: PyGePoint3d) -> None:
        self._obj.AppendVertex(Point())
    
    def Explode(self) -> vObjectArray:
        return vObjectArray(self._obj.Explode())

    def GetBulge(self, Index: int) -> float:
        return self._obj.GetBulge(Index)
        
    def GetWidth(self, Index: int) -> vDoubleArray:
        StartWidth, EndWidth = self._obj.GetWidth(Index)
        return vDoubleArray(StartWidth, EndWidth)
        
    def Offset(self, Distance: float) -> vObjectArray:
        return vObjectArray(self._obj.Offset(Distance))

    def SetBulge(self, Index: int, Value: float) -> None:
        self._obj.SetBulge(Index, Value)

    def SetWidth(self, SegmentIndex: int, StartWidth: float, EndWidth: float) -> None:
        self._obj.SetBulge(SegmentIndex, StartWidth, EndWidth)