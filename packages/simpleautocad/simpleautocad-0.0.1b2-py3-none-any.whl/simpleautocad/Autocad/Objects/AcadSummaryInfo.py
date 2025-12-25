from __future__ import annotations
from ..Base import *
from ..Proxy import *



class AcadSummaryInfo(AppObject):
    def __init__(self, obj) -> None: super().__init__(obj)

    Author: str = proxy_property(str,'Author',AccessMode.ReadWrite)
    Comments: str = proxy_property(str,'Comments',AccessMode.ReadWrite)
    HyperlinkBase: str = proxy_property(str,'HyperlinkBase',AccessMode.ReadWrite)
    Keywords: str = proxy_property(str,'Keywords',AccessMode.ReadWrite)
    LastSavedBy: str = proxy_property(str,'LastSavedBy',AccessMode.ReadWrite)
    RevisionNumber: str = proxy_property(str,'RevisionNumber',AccessMode.ReadWrite)
    Subject: str = proxy_property(str,'Subject',AccessMode.ReadWrite)
    Title: str = proxy_property(str,'Title',AccessMode.ReadWrite)

    def AddCustomInfo(self, key: str, Value: str) -> None:
        self._obj.AddCustomInfo(key, Value)

    def GetCustomByIndex(self, Index: int) -> str:
        pKey, pValue = self._obj.GetCustomByIndex(Index)
        return pKey, pValue

    def GetCustomByKey(self, pKey: str) -> vStringArray:
        pValue = self._obj.GetCustomByKey(pKey)
        return vStringArray(pValue)

    def NumCustomInfo(self) -> int:
        return self._obj.NumCustomInfo()

    def RemoveCustomByIndex(self, Index: int) -> None:
        self._obj.RemoveCustomByIndex(Index)

    def RemoveCustomByKey(self, key: str) -> None:
        self._obj.RemoveCustomByKey(key)

    def SetCustomByIndex(self, Index: int, key: str, Value: str) -> None:
        self._obj.SetCustomByIndex(Index, key, Value)

    def SetCustomByKey(self, key: str, Value: str) -> None:
        self._obj.SetCustomByKey(key, Value)