from __future__ import annotations
from ..Base import *
from ..Proxy import proxy_property, AccessMode
from ..AcadObject import *



class AcadViewport(AcadObject):
    def __init__(self, obj) -> None: super().__init__(obj)

    ArcSmoothness: int = proxy_property(int,'ArcSmoothness',AccessMode.ReadWrite)
    Center: PyGePoint2d = proxy_property('PyGePoint2d','Center',AccessMode.ReadWrite)
    Direction: PyGeVector3d = proxy_property('PyGeVector3d','Direction',AccessMode.ReadWrite)
    GridOn: bool = proxy_property(bool,'GridOn',AccessMode.ReadWrite)
    Height: float = proxy_property(float,'Height',AccessMode.ReadWrite)
    LowerLeftCorner: vDoubleArray = proxy_property('vDoubleArray','LowerLeftCorner',AccessMode.ReadOnly)
    Name: str = proxy_property(str,'Name',AccessMode.ReadWrite)
    OrthoOn: bool = proxy_property(bool,'OrthoOn',AccessMode.ReadWrite)
    SnapBasePoint: vDoubleArray = proxy_property('vDoubleArray','SnapBasePoint',AccessMode.ReadWrite)
    SnapOn: bool = proxy_property(bool,'SnapOn',AccessMode.ReadWrite)
    SnapRotationAngle: float = proxy_property(float,'SnapRotationAngle',AccessMode.ReadWrite)
    Target: PyGePoint3d = proxy_property('PyGePoint3d','Target',AccessMode.ReadWrite)
    UCSIconAtOrigin: bool = proxy_property(bool,'UCSIconAtOrigin',AccessMode.ReadWrite)
    UCSIconOn: bool = proxy_property(bool,'UCSIconOn',AccessMode.ReadWrite)
    UpperRightCorner: vDoubleArray = proxy_property('vDoubleArray','UpperRightCorner',AccessMode.ReadOnly)
    Width: float = proxy_property(float,'Width',AccessMode.ReadWrite)

    def GetGridSpacing(self) -> vDoubleArray: 
        XSpacing, YSpacing = self._obj.GetGridSpacing()
        return vDoubleArray(XSpacing, YSpacing)
        
    def GetSnapSpacing(self) -> vDoubleArray: 
        XSpacing, YSpacing = self._obj.GetSnapSpacing()
        return vDoubleArray(XSpacing, YSpacing)
        
    def SetGridSpacing(self, XSpacing: float, YSpacing: float) -> None: 
        self._obj.SetGridSpacing(XSpacing, YSpacing)

    def SetSnapSpacing(self, XSpacing: float, YSpacing: float) -> None: 
        self._obj.SetSnapSpacing(XSpacing, YSpacing)

    def SetView(self, View: AcadView) -> None: 
        self._obj.SetView(View())

    def Split(self, NumWins: AcViewportSplitType) -> None: 
        self._obj.Split(NumWins)