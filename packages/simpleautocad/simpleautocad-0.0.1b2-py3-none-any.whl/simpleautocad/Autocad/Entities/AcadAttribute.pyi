from ..Base import *
from ..Proxy import *
from ..AcadEntity import AcadEntity as AcadEntity

class AcadAttribute(AcadEntity):
    def __init__(self, obj) -> None: ...
    Alignment: AcAlignment
    Backward: bool
    Constant: bool
    FieldLength: int
    Height: float
    InsertionPoint: PyGePoint3d
    Invisible: bool
    LockPosition: bool
    Mode: AcAttributeMode
    MTextAttribute: bool
    MTextAttributeContent: str
    MTextBoundaryWidth: float
    MTextDrawingDirection: AcDrawingDirection
    Normal: PyGeVector3d
    ObliqueAngle: float
    Preset: bool
    PromptString: str
    Rotation: float
    ScaleFactor: float
    StyleName: str
    TagString: str
    TextAlignmentPoint: PyGePoint3d
    TextGenerationFlag: AcTextGenerationFlag
    TextString: str
    Thickness: float
    UpsideDown: bool
    Verify: bool
    def Copy(self) -> AcadAttribute: ...
    def UpdateMTextAttribute(self) -> None: ...
