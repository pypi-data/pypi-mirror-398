from __future__ import annotations
from ..Base import *
from ..Proxy import *
from ..AcadEntity import AcadEntity
from abc import ABC, abstractmethod



class AcadUnderlay(AcadEntity, ABC):
    def __init__(self, obj) -> None: super().__init__(obj)

    AdjustForBackground: bool = proxy_property(bool,'AdjustForBackground',AccessMode.ReadWrite)
    ClippingEnabled: bool = proxy_property(bool,'ClippingEnabled',AccessMode.ReadWrite)
    Contrast: int = proxy_property(int,'Contrast',AccessMode.ReadWrite)
    Fade: int = proxy_property(int,'Fade',AccessMode.ReadWrite)
    File: str = proxy_property(str,'File',AccessMode.ReadWrite)
    Height: float = proxy_property(float,'Height',AccessMode.ReadWrite)
    ItemName: str = proxy_property(str,'ItemName',AccessMode.ReadWrite)
    Monochrome: bool = proxy_property(bool,'Monochrome',AccessMode.ReadWrite)
    Position: PyGePoint3d = proxy_property('PyGePoint3d','Position',AccessMode.ReadWrite)
    Rotation: float = proxy_property(float,'Rotation',AccessMode.ReadWrite)
    ScaleFactor: float = proxy_property(float,'ScaleFactor',AccessMode.ReadWrite)
    UnderlayLayerOverrideApplied: bool = proxy_property(bool,'UnderlayLayerOverrideApplied',AccessMode.ReadWrite)
    UnderlayName: str = proxy_property(str,'UnderlayName',AccessMode.ReadWrite)
    UnderlayVisibility: bool = proxy_property(bool,'UnderlayVisibility',AccessMode.ReadWrite)
    Width: float = proxy_property(float,'Width',AccessMode.ReadWrite)

    def ClipBoundary(self, PointsArray: PyGePoint3dArray) -> None:
        self._obj.ClipBoundary(PointsArray)
    
    @abstractmethod
    def Copy(self): return self._obj.Copy()
