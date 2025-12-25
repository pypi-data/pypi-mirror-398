from __future__ import annotations
from ..Base import *
from ..Proxy import *
from ..AcadEntity import AcadEntity



class Acad3DFace(AcadEntity):
    def __init__(self, obj) -> None: super().__init__(obj)

    Coordinates: PyGePoint3dArray = proxy_property('PyGePoint3dArray','Coordinates',AccessMode.ReadWrite)
    VisibilityEdge1: bool = proxy_property(bool,'VisibilityEdge1',AccessMode.ReadWrite)
    VisibilityEdge2: bool = proxy_property(bool,'VisibilityEdge2',AccessMode.ReadWrite)
    VisibilityEdge3: bool = proxy_property(bool,'VisibilityEdge3',AccessMode.ReadWrite)
    VisibilityEdge4: bool = proxy_property(bool,'VisibilityEdge4',AccessMode.ReadWrite)
    

    def Coordinate(self, Index: int) -> PyGePoint3d:
        return PyGePoint3d(self._obj.Coordinate(Index))

    def Copy(self) -> Acad3DFace:
        return Acad3DFace(self._obj.Copy())
        
    def GetInvisibleEdge(self, Index: int) -> bool:
        return self._obj.GetInvisibleEdge(Index)
        
    def SetInvisibleEdge(self, Index: int, State: bool) -> None:
        self._obj.SetInvisibleEdge(Index, State)