from ..Base import *
from ..Proxy import *
import abc
from ..AcadEntity import AcadEntity as AcadEntity
from abc import ABC, abstractmethod

class AcadUnderlay(AcadEntity, ABC, metaclass=abc.ABCMeta):
    def __init__(self, obj) -> None: ...
    AdjustForBackground: bool
    ClippingEnabled: bool
    Contrast: int
    Fade: int
    File: str
    Height: float
    ItemName: str
    Monochrome: bool
    Position: PyGePoint3d
    Rotation: float
    ScaleFactor: float
    UnderlayLayerOverrideApplied: bool
    UnderlayName: str
    UnderlayVisibility: bool
    Width: float
    def ClipBoundary(self, PointsArray: PyGePoint3dArray) -> None: ...
    @abstractmethod
    def Copy(self): ...
