from ..Base import *
from ..Proxy import *
from ..AcadEntity import AcadEntity as AcadEntity

class AcadMtext(AcadEntity):
    def __init__(self, obj) -> None: ...
    AttachmentPoint: AcAttachmentPoint
    BackgroundFill: bool
    DrawingDirection: AcDrawingDirection
    Height: float
    InsertionPoint: PyGePoint3d
    LineSpacingDistance: float
    LineSpacingFactor: float
    LineSpacingStyle: AcLineSpacingStyle
    Normal: PyGeVector3d
    TextString: str
    Width: float
    def FieldCode(self) -> str: ...
    def Copy(self) -> AcadMtext: ...
