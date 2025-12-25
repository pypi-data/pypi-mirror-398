from __future__ import annotations
from ..Base import *
from ..Proxy import *
from ..AcadObject import *

class AcadPopupMenu(AppObject):
    def __init__(self, obj) -> None: super().__init__(obj)

    Application: AcadApplication = proxy_property('AcadApplication','Application',AccessMode.ReadOnly)
    Count: int = proxy_property(int,'Count',AccessMode.ReadOnly)
    Name: str = proxy_property(str,'Name',AccessMode.ReadWrite)
    NameNoMnemonic: str = proxy_property(str,'NameNoMnemonic',AccessMode.ReadOnly)
    OnMenuBar: bool = proxy_property(bool,'OnMenuBar',AccessMode.ReadOnly)
    Parent: AppObject = proxy_property('AppObject','Parent',AccessMode.ReadWrite)
    ShortcutMenu: bool = proxy_property(bool,'ShortcutMenu',AccessMode.ReadWrite)
    TagString: str = proxy_property(str,'TagString',AccessMode.ReadOnly)

    def AddMenuItem(self, Index: int | str, Label: str, Macro: str) -> AcadPopupMenuItem: 
        return AcadPopupMenuItem(self._obj.AddMenuItem(Index, Label, Macro))

    def AddSeparator(self, Index: int | str) -> AcadPopupMenuItem: 
        return AcadPopupMenuItem(self._obj.AddSeparator(Index))

    def AddSubMenu(self, Index: int | str, Label: str) -> AcadPopupMenu: 
        return AcadPopupMenu(self._obj.AddSubMenu(Index, Label))

    def InsertInMenuBar(self, Index: int | str) -> None: 
        self._obj.InsertInMenuBar(Index)

    def Item(self, Index: int | str) -> AcadPopupMenu: 
        return AcadPopupMenu(self._obj.Item(Index))

    def RemoveMenuFromMenuBar(self, Index: int) -> None: 
        self._obj.RemoveMenuFromMenuBar(Index)
