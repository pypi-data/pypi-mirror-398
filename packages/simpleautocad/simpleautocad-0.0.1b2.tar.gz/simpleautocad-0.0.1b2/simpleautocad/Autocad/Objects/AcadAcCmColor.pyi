from ..AcadObject import *
from ..Proxy import AccessMode as AccessMode, proxy_property as proxy_property

class AcadAcCmColor(AppObject):
    def __init__(self, obj) -> None: ...
    Blue: int
    BookName: str
    ColorIndex: AcColor
    ColorMethod: AcColorMethod
    ColorName: str
    EntityColor: int
    Green: int
    Red: int
    def Delete(self) -> None: ...
    def SetColorBookColor(self, BookName: str, ColorName: str) -> None: ...
    def SetNames(self, ColorName: str, ColorBook: str) -> None: ...
    def SetRGB(self, Red: int, Green: int, Blue: int) -> None: ...
