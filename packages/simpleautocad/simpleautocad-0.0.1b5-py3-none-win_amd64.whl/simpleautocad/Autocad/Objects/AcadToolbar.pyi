from ..Base import *
from ..Proxy import *
from ..AcadObject import *

class AcadToolbar(AppObject):
    def __init__(self, obj) -> None: ...
    Application: AcadApplication
    Count: int
    DockStatus: AcToolbarDockStatus
    FloatingRows: int
    Height: int
    HelpString: str
    LargeButtons: bool
    Left: int
    Name: str
    Parent: AppObject
    TagString: str
    Top: int
    Visible: bool
    Width: float
    def AddSeparator(self, Index: int | str) -> AcadToolbarItem: ...
    def AddToolbarButton(self, Index: int | str, Name: str, HelpString: str, Macro: str, FlyoutButton: vBool = None) -> AcadToolbarItem: ...
    def Delete(self) -> None: ...
    def Dock(self, Side: AcToolbarDockStatus) -> None: ...
    def Float(self, Top: int, Left: int, NumberFloatRows: int) -> None: ...
    def Item(self, Index: int | str) -> AcadObject: ...
