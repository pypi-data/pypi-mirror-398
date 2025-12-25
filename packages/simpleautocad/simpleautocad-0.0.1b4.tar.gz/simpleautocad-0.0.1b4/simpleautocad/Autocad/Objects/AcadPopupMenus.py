from __future__ import annotations
from ..Base import *
from ..Proxy import *
from .AcadPopupMenu import *

class AcadPopupMenus(AppObject):
    def __init__(self, obj) -> None: super().__init__(obj)

    Application: AcadApplication = proxy_property('AcadApplication','Application',AccessMode.ReadOnly)
    Count: int = proxy_property(int,'Count',AccessMode.ReadOnly)
    Parent: AppObject = proxy_property('AppObject','Parent',AccessMode.ReadWrite)

    def Add(self, Name: str) -> AcadPopupMenu: 
        return AcadPopupMenu(self._obj.Add(Name))

    def InsertMenuInMenuBar(self, MenuName: str, Index: int) -> None: 
        self._obj.InsertMenuInMenuBar(MenuName, Index)

    def Item(self, Index: int) -> AcadPopupMenu: 
        return AcadPopupMenu(self._obj.Item(Index))

    def RemoveMenuFromMenuBar(self, Index: int) -> None: 
        self._obj.RemoveMenuFromMenuBar(Index)

    def __iter__(self):
        for item in self._obj:
            obj = AcadPopupMenu(item)
            yield obj