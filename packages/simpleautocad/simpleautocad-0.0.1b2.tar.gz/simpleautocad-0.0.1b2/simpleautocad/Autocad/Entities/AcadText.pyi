from ..Base import *
from ..Proxy import *
from ..AcadEntity import AcadEntity as AcadEntity

class AcadText(AcadEntity):
    def __init__(self, obj) -> None: ...
    Alignment: AcAlignment
    Backward: bool
    Height: float
    InsertionPoint: PyGePoint3d
    Normal: PyGeVector3d
    ObliqueAngle: float
    TextAlignmentPoint: PyGePoint3d
    TextGenerationFlag: AcTextGenerationFlag
    TextString: str
    Thickness: float
    UpsideDown: bool
    def Copy(self) -> AcadText: ...
    def FieldCode(self) -> str: ...
