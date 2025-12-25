from __future__ import annotations
from ..Proxy import *
from ..AcadObject import AcadObject
from .AcadXRecord import AcadXRecord


class AcadDictionary(AcadObject):
    def __init__(self, obj) -> None: super().__init__(obj)

    Name: str = proxy_property(str,'Name',AccessMode.ReadOnly)
    Count: int = proxy_property(int,'Count',AccessMode.ReadOnly)

    def AddObject(self, Keyword: str, ObjectName: str) -> AcadObject: 
        return AcadObject(self._obj.AddObject(Keyword, ObjectName))

    def AddXRecord(self, Keyword: str) -> AcadXRecord: 
        return AcadXRecord(self._obj.AddXRecord(Keyword))

    def GetName(self, Object: AppObject) -> str: 
        return self._obj.GetName(Object())

    def GetObject(self, Name: str) -> AcadObject: 
        return AcadObject(self._obj.GetObject(Name))

    def Item(self, Index: int | str) -> AcadObject: 
        return AcadObject(self._obj.Item(Index))

    def Remove(self, Name: str) -> AcadObject: 
        return AcadObject(self._obj.Remove(Name))

    def Rename(self, OldName: str, NewName: str) -> None: 
        self._obj.Rename(OldName, NewName)
        
    def Replace(self, Name: str, NewObject: AppObject) -> None: 
        self._obj.Replace(Name, NewObject())
