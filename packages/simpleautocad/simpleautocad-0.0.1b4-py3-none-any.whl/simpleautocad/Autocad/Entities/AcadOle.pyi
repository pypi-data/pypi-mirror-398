from ..Base import *
from ..Proxy import *
from ..AcadEntity import AcadEntity as AcadEntity

class AcadOle(AcadEntity):
    def __init__(self, obj) -> None: ...
    Height: float
    InsertionPoint: PyGePoint3d
    LockAspectRatio: bool
    OleItemType: AcOleType
    OlePlotQuality: AcOlePlotQuality
    OleSourceApp: str
    Rotation: float
    ScaleHeight: float
    ScaleWidth: float
    Width: float
    def Copy(self) -> AcadOle: ...
