from ..Base import *
from ..Proxy import *
from ..AcadEntity import AcadEntity as AcadEntity

class AcadRasterImage(AcadEntity):
    def __init__(self, obj) -> None: ...
    Brightness: int
    ClippingEnabled: bool
    Contrast: int
    Fade: int
    Height: float
    ImageFile: str
    ImageHeight: float
    ImageVisibility: bool
    ImageWidth: float
    Name: str
    Origin: PyGePoint3d
    Rotation: float
    ScaleFactor: float
    ShowRotation: bool
    Transparency: bool
    Width: float
    def ClipBoundary(self, PointsArray: PyGePoint2dArray) -> None: ...
    def Copy(self) -> AcadRasterImage: ...
