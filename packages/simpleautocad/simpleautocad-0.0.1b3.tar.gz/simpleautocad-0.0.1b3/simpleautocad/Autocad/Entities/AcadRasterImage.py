from __future__ import annotations
from ..Base import *
from ..Proxy import *
from ..AcadEntity import AcadEntity



class AcadRasterImage(AcadEntity):
    def __init__(self, obj) -> None: super().__init__(obj)

    Brightness: int = proxy_property(int,'Brightness',AccessMode.ReadWrite)
    ClippingEnabled: bool = proxy_property(bool,'ClippingEnabled',AccessMode.ReadWrite)
    Contrast: int = proxy_property(int,'Contrast',AccessMode.ReadWrite)
    Fade: int = proxy_property(int,'Fade',AccessMode.ReadWrite)
    Height: float = proxy_property(float,'Height',AccessMode.ReadOnly)
    ImageFile: str = proxy_property(str,'ImageFile',AccessMode.ReadWrite)
    ImageHeight: float = proxy_property(float,'ImageHeight',AccessMode.ReadWrite)
    ImageVisibility: bool = proxy_property(bool,'ImageVisibility',AccessMode.ReadWrite)
    ImageWidth: float = proxy_property(float,'ImageWidth',AccessMode.ReadWrite)
    Name: str = proxy_property(str,'Name',AccessMode.ReadWrite)
    Origin: PyGePoint3d = proxy_property('PyGePoint3d','Origin',AccessMode.ReadWrite)
    Rotation: float = proxy_property(float,'Rotation',AccessMode.ReadWrite)
    ScaleFactor: float = proxy_property(float,'ScaleFactor',AccessMode.ReadWrite)
    ShowRotation: bool = proxy_property(bool,'ShowRotation',AccessMode.ReadWrite)
    Transparency: bool = proxy_property(bool,'Transparency',AccessMode.ReadWrite)
    Width: float = proxy_property(float,'Width',AccessMode.ReadOnly)

    def ClipBoundary(self, PointsArray: PyGePoint2dArray) -> None:
        self._obj.ClipBoundary(PointsArray())

    def Copy(self) -> AcadRasterImage:
        return AcadRasterImage(self._obj.Copy())

