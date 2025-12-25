from __future__ import annotations
from ..Base import *
from ..Proxy import *
from ..AcadObject import *

class AcadState(AppObject):
    def __init__(self, obj) -> None: super().__init__(obj)
    
    Application: AcadApplication = proxy_property('AcadApplication','Application',AccessMode.ReadOnly)
    IsQuiescent: bool = proxy_property(bool,'IsQuiescent',AccessMode.ReadOnly)
