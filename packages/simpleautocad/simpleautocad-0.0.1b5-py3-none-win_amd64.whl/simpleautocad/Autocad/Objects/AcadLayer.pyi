from ..Base import *
from ..Proxy import *
from ..AcadObject import *

class AcadLayer(AcadObject):
    def __init__(self, obj) -> None: ...
    Application: AcadApplication
    Description: str
    Document: AcadDocument
    Freeze: bool
    Handle: int
    HasExtensionDictionary: bool
    LayerOn: bool
    Linetype: str
    Lineweight: AcLineWeight
