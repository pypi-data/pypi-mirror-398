from __future__ import annotations
from ..Base import *
from ..AcadObject import *
from ..Proxy import *
from .AcadDocument import AcadDocument



class AcadDocuments(IAcadObjectCollection):
    def __init__(self, obj) -> None: super().__init__(obj)

    Application: AcadApplication = proxy_property('AcadApplication','Application',AccessMode.ReadOnly)
    Count: int = proxy_property(int,'Count',AccessMode.ReadOnly)

    def Add(self, Name: str = '') -> AcadDocument: 
        return AcadDocument(self._obj.Add(Name))

    def Close(self) -> None: 
        self._obj.Close()

    def Item(self, Index: int) -> AcadDocument: 
        return AcadDocument(self._obj.Item(Index))

    def Open(self, Name: str, ReadOnly: bool = False, Password: Variant = vObjectEmpty) -> AcadDocument: 
        return AcadDocument(self._obj.Open(Name, ReadOnly, Password()))
    
    def __iter__(self):
        for item in self._obj:
            obj = AcadDocument(item)
            yield obj