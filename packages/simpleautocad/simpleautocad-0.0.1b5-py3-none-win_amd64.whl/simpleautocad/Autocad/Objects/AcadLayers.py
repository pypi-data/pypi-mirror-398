from __future__ import annotations
from ..Base import *
from ..Proxy import *
from ..AcadObject import *



class AcadLayers(IAcadObjectCollection):
    def __init__(self, obj) -> None: super().__init__(obj)

    # Application: AcadApplication = proxy_property('AcadApplication','Application',AccessMode.ReadOnly)
    # Count: int = proxy_property(int,'Count',AccessMode.ReadOnly)
    # Document: AcadDocument = proxy_property('AcadDocument','Document',AccessMode.ReadOnly)
    # Handle: int = proxy_property(int,'Handle',AccessMode.ReadOnly)
    # HasExtensionDictionary: bool = proxy_property(bool,'HasExtensionDictionary',AccessMode.ReadOnly)
    # ObjectID: int = proxy_property(int,'ObjectID',AccessMode.ReadOnly)
    # ObjectName: str = proxy_property(str,'ObjectName',AccessMode.ReadOnly)
    # OwnerID: int = proxy_property(int,'OwnerID',AccessMode.ReadOnly)

    def Add(self, Name: str) -> AcadLayer: 
        return AcadLayer(self._obj.Add(Name))

    def Item(self, Index: int | str) -> AcadLayer:
        return AcadLayer(self._obj.Item(Index))

    def __iter__(self):
        for item in self._obj:
            obj = AcadLayer(item)
            yield obj

