from ..Base import *
from ..Proxy import *
from ..AcadObject import *
from .AcadToolbar import *

class AcadToolbarItem(AppObject):
    def __init__(self, obj) -> None: ...
    Application: AcadApplication
    CommandDisplayName: str
    Flyout: AcadToolbar
    HelpString: str
    Index: int
    Macro: str
    Name: str
    Parent: AppObject
    TagString: str
    Type: AcToolbarItemType
    def AttachToolbarToFlyout(self, MenuGroupName: str, ToolbarName: str) -> None: ...
    def Delete(self) -> None: ...
    def GetBitmaps(self) -> tuple[str]: ...
    def SetBitmaps(self, SmallIconName: str, LargeIconName: str) -> None: ...
