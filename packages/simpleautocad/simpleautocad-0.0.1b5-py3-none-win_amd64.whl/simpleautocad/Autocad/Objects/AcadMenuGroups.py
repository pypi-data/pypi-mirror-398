from __future__ import annotations
from ..Base import *
from ..Proxy import proxy_property, AccessMode
from ..AcadObject import *
from .AcadMenuGroup import *



class AcadMenuGroups(AppObjectCollection):
    def __init__(self, obj) -> None: super().__init__(obj)

    Application: 'AcadApplication' = proxy_property('AcadApplication','Application',AccessMode.ReadOnly)
    Count: int = proxy_property(int,'Count',AccessMode.ReadOnly)
    Parent: AppObject = proxy_property('AppObject','Parent',AccessMode.ReadWrite)

    def Item(self, Index: int | str) -> AcadMenuGroup: 
        return AcadMenuGroup(self._obj.Item(Index))

    def Load(self, MenuFileName: str, BaseMenu: bool = None) -> AcadMenuGroup: 
        if BaseMenu:
            return AcadMenuGroup(self._obj.Load(MenuFileName, BaseMenu))
        return AcadMenuGroup(self._obj.Load(MenuFileName))

    def __iter__(self):
        for item in self._obj:
            obj = AcadMenuGroup(item)
            yield obj