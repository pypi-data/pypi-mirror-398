from ..Base import *
from ..Proxy import *
from .AcadPopupMenu import *

class AcadPopupMenuItem(AppObject):
    def __init__(self, obj) -> None: ...
    Application: AcadApplication
    Caption: str
    Check: bool
    Enable: bool
    EndSubMenuLevel: int
    HelpString: str
    Index: str
    Label: str
    Parent: AppObject
    SubMenu: AcadPopupMenu
    TagString: str
    Type: AcMenuItemType
    def Delete(self) -> None: ...
