from __future__ import annotations
from ..Base import *
from ..Proxy import *
from ..AcadEntity import AcadEntity



class AcadMLine(AcadEntity):
    def __init__(self, obj) -> None: super().__init__(obj)

    Coordinates: PyGePoint3d = proxy_property('PyGePoint3d','Coordinates',AccessMode.ReadWrite)
    Justification: AcMLineJustification = proxy_property('AcMLineJustification','Justification',AccessMode.ReadWrite)
    MLineScale: float = proxy_property(float,'MLineScale',AccessMode.ReadWrite)
    StyleName: str = proxy_property(str,'StyleName',AccessMode.ReadOnly)

    def Copy(self) -> AcadMtext:
        return AcadMtext(self._obj.Copy())