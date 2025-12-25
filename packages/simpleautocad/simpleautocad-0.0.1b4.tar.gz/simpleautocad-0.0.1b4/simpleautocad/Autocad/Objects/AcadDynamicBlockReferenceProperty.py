from __future__ import annotations
from ..Base import *
from ..Proxy import *



class AcadDynamicBlockReferenceProperty(AppObject):
    def __init__(self, obj) -> None: super().__init__(obj)

    AllowedValues: any = proxy_property(any,'AllowedValues',AccessMode.ReadOnly)
    Description: str = proxy_property(str,'Description',AccessMode.ReadOnly)
    PropertyName: str = proxy_property(str,'PropertyName',AccessMode.ReadOnly)
    ReadOnly: bool = proxy_property(bool,'ReadOnly',AccessMode.ReadOnly)
    Show: bool = proxy_property(bool,'Show',AccessMode.ReadOnly)
    UnitsType: AcDynamicBlockReferencePropertyUnitsType  = proxy_property('AcDynamicBlockReferencePropertyUnitsType','UnitsType',AccessMode.ReadOnly)
    Value: any  = proxy_property(any,'Value',AccessMode.ReadWrite)
