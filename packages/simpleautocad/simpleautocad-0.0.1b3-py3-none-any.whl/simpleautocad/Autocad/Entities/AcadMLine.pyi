from ..Base import *
from ..Proxy import *
from ..AcadEntity import AcadEntity as AcadEntity

class AcadMLine(AcadEntity):
    def __init__(self, obj) -> None: ...
    Coordinates: PyGePoint3d
    Justification: AcMLineJustification
    MLineScale: float
    StyleName: str
    def Copy(self) -> AcadMtext: ...
