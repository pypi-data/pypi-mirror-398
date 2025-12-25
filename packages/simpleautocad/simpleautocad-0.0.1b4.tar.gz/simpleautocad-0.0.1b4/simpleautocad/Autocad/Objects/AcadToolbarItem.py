from __future__ import annotations
from ..Base import *
from ..Proxy import *
from ..AcadObject import *
from .AcadToolbar import *

class AcadToolbarItem(AppObject):
    def __init__(self, obj) -> None: super().__init__(obj)

    Application: AcadApplication = proxy_property('AcadApplication','Application',AccessMode.ReadOnly)
    CommandDisplayName: str = proxy_property(str,'CommandDisplayName',AccessMode.ReadWrite)
    Flyout: AcadToolbar = proxy_property('AcadToolbar','Flyout',AccessMode.ReadOnly)
    HelpString: str = proxy_property(str,'HelpString',AccessMode.ReadWrite)
    Index: int = proxy_property(int,'Index',AccessMode.ReadOnly)
    Macro: str = proxy_property(str,'Macro',AccessMode.ReadWrite)
    Name: str = proxy_property(str,'Name',AccessMode.ReadWrite)
    Parent: AppObject = proxy_property('AppObject','Parent',AccessMode.ReadWrite)
    TagString: str = proxy_property(str,'TagString',AccessMode.ReadWrite)
    Type: AcToolbarItemType = proxy_property('AcToolbarItemType','Type',AccessMode.ReadOnly)

    def AttachToolbarToFlyout(self, MenuGroupName: str, ToolbarName: str) -> None:
        self._obj.AttachToolbarToFlyout(MenuGroupName, ToolbarName)

    def Delete(self) -> None:
        self._obj.Delete()

    def GetBitmaps(self) -> tuple[str]:
        SmallIconName, LargeIconName = self._obj.GetBitmaps()
        return SmallIconName, LargeIconName

    def SetBitmaps(self, SmallIconName: str, LargeIconName: str) -> None:
        self._obj.SetBitmaps(SmallIconName, LargeIconName)
