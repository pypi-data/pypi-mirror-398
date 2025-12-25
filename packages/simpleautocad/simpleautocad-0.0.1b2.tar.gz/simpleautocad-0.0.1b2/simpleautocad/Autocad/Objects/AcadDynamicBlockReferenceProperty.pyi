from ..Base import *
from ..Proxy import *

class AcadDynamicBlockReferenceProperty(AppObject):
    def __init__(self, obj) -> None: ...
    AllowedValues: any
    Description: str
    PropertyName: str
    ReadOnly: bool
    Show: bool
    UnitsType: AcDynamicBlockReferencePropertyUnitsType
    Value: any
