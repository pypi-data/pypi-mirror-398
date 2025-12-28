from __future__ import annotations
from ..Base import *
from ..Proxy import proxy_property, AccessMode
from ..AcadObject import *



class AcadTextStyle(AcadObject):
    def __init__(self, obj) -> None: super().__init__(obj)

    BigFontFile: str = proxy_property(str,'BigFontFile',AccessMode.ReadWrite)
    FontFile: str = proxy_property(str,'FontFile',AccessMode.ReadWrite)
    Height: float = proxy_property(float,'Height',AccessMode.ReadWrite)
    LastHeight: float = proxy_property(float,'LastHeight',AccessMode.ReadWrite)
    Name: str = proxy_property(str,'Name',AccessMode.ReadOnly)
    ObliqueAngle: float = proxy_property(float,'ObliqueAngle',AccessMode.ReadWrite)
    TextGenerationFlag: AcTextGenerationFlag = proxy_property('AcTextGenerationFlag','TextGenerationFlag',AccessMode.ReadWrite)
    Width: float = proxy_property(float,'Width',AccessMode.ReadWrite)

    def GetFont(self) -> tuple[str,bool,bool,int,int]:
        Typeface, Bold, Italic, CharSet, PitchAndFamily = self._obj.GetFont()
        return Typeface, Bold, Italic, CharSet, PitchAndFamily

    def SetFont(self, Typeface: str, Bold: bool, Italic: bool, CharSet: int, PitchAndFamily: int) -> None:
        self._obj.SetFont(Typeface, Bold, Italic, CharSet, PitchAndFamily)
