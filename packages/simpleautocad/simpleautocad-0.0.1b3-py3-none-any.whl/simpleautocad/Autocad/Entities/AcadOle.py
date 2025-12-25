from __future__ import annotations
from ..Base import *
from ..Proxy import *
from ..AcadEntity import AcadEntity



class AcadOle(AcadEntity):
    def __init__(self, obj) -> None: super().__init__(obj)

    Height: float = proxy_property(float,'Height',AccessMode.ReadWrite)
    InsertionPoint: PyGePoint3d = proxy_property('PyGePoint3d','InsertionPoint',AccessMode.ReadWrite)
    LockAspectRatio: bool = proxy_property(bool,'LockAspectRatio',AccessMode.ReadWrite)
    OleItemType: AcOleType = proxy_property('AcOleType','OleItemType',AccessMode.ReadWrite)
    OlePlotQuality: AcOlePlotQuality = proxy_property('AcOlePlotQuality','OlePlotQuality',AccessMode.ReadWrite)
    OleSourceApp: str = proxy_property(str,'OleSourceApp',AccessMode.ReadWrite)
    Rotation: float = proxy_property(float,'Rotation',AccessMode.ReadWrite)
    ScaleHeight: float = proxy_property(float,'ScaleHeight',AccessMode.ReadWrite)
    ScaleWidth: float = proxy_property(float,'ScaleWidth',AccessMode.ReadWrite)
    Width: float = proxy_property(float,'Width',AccessMode.ReadWrite)

    def Copy(self) -> AcadOle:
        return AcadOle(self._obj.Copy())
