from ..Base import *
from ..AcadObject import *
from ..Proxy import AccessMode as AccessMode, proxy_property as proxy_property

class AcadTextStyle(AcadObject):
    def __init__(self, obj) -> None: ...
    BigFontFile: str
    FontFile: str
    Height: float
    LastHeight: float
    Name: str
    ObliqueAngle: float
    TextGenerationFlag: AcTextGenerationFlag
    Width: float
    def GetFont(self) -> tuple[str, bool, bool, int, int]: ...
    def SetFont(self, Typeface: str, Bold: bool, Italic: bool, CharSet: int, PitchAndFamily: int) -> None: ...
