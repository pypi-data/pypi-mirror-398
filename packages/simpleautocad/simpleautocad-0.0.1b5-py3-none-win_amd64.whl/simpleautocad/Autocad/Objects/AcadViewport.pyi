from ..Base import *
from ..AcadObject import *
from ..Proxy import AccessMode as AccessMode, proxy_property as proxy_property

class AcadViewport(AcadObject):
    def __init__(self, obj) -> None: ...
    ArcSmoothness: int
    Center: PyGePoint2d
    Direction: PyGeVector3d
    GridOn: bool
    Height: float
    LowerLeftCorner: vDoubleArray
    Name: str
    OrthoOn: bool
    SnapBasePoint: vDoubleArray
    SnapOn: bool
    SnapRotationAngle: float
    Target: PyGePoint3d
    UCSIconAtOrigin: bool
    UCSIconOn: bool
    UpperRightCorner: vDoubleArray
    Width: float
    def GetGridSpacing(self) -> vDoubleArray: ...
    def GetSnapSpacing(self) -> vDoubleArray: ...
    def SetGridSpacing(self, XSpacing: float, YSpacing: float) -> None: ...
    def SetSnapSpacing(self, XSpacing: float, YSpacing: float) -> None: ...
    def SetView(self, View: AcadView) -> None: ...
    def Split(self, NumWins: AcViewportSplitType) -> None: ...
