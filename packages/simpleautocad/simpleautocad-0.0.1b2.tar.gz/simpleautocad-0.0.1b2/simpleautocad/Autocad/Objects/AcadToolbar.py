from __future__ import annotations
from ..Base import *
from ..Proxy import *
from ..AcadObject import *

class AcadToolbar(AppObject):
    def __init__(self, obj) -> None: super().__init__(obj)

    Application: AcadApplication = proxy_property('AcadApplication','Application',AccessMode.ReadOnly)
    Count: int = proxy_property(int,'Count',AccessMode.ReadOnly)
    DockStatus: AcToolbarDockStatus = proxy_property('AcToolbarDockStatus','DockStatus',AccessMode.ReadOnly)
    FloatingRows: int = proxy_property(int,'FloatingRows',AccessMode.ReadWrite)
    Height: int = proxy_property(int,'Height',AccessMode.ReadOnly)
    HelpString: str = proxy_property(str,'HelpString',AccessMode.ReadWrite)
    LargeButtons: bool = proxy_property(bool,'LargeButtons',AccessMode.ReadOnly)
    Left: int = proxy_property(int,'Left',AccessMode.ReadWrite)
    Name: str = proxy_property(str,'Name',AccessMode.ReadWrite)
    Parent: AppObject = proxy_property('AppObject','Parent',AccessMode.ReadWrite)
    TagString: str = proxy_property(str,'TagString',AccessMode.ReadOnly)
    Top: int = proxy_property(int,'Top',AccessMode.ReadWrite)
    Visible: bool = proxy_property(bool,'Visible',AccessMode.ReadWrite)
    Width: float = proxy_property(float,'Width',AccessMode.ReadOnly)

    def AddSeparator(self, Index: int | str) -> AcadToolbarItem:
        return AcadToolbarItem(self._obj.AddSeparator(Index))

    def AddToolbarButton(self, Index: int | str, Name: str, HelpString: str, Macro: str, FlyoutButton: vBool = None) -> AcadToolbarItem:
        if FlyoutButton is None:
            return AcadToolbarItem(self._obj.AddToolbarButton(Index, Name, HelpString, Macro))
        else:
            return AcadToolbarItem(self._obj.AddToolbarButton(Index, Name, HelpString, Macro, FlyoutButton()))

    def Delete(self) -> None:
        self._obj.Delete()

    def Dock(self, Side: AcToolbarDockStatus) -> None:
        self._obj.Dock(Side)

    def Float(self, Top: int, Left: int, NumberFloatRows: int) -> None:
        self._obj.Float(Top, Left, NumberFloatRows)

    def Item(self, Index: int | str) -> AcadObject:
        return AcadObject(self._obj.Item(Index))
