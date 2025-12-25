from __future__ import annotations
from ..Base import *
from ..Proxy import *
from ..AcadObject import *

class AcadIDPair(AppObject):
    def __init__(self, obj) -> None: super().__init__(obj)

    Application: AcadApplication = proxy_property('AcadApplication','Application',AccessMode.ReadOnly)
    IsCloned: bool = proxy_property(bool,'IsCloned',AccessMode.ReadOnly)
    IsOwnerXlated: bool = proxy_property(bool,'IsOwnerXlated',AccessMode.ReadOnly)
    IsPrimary: bool = proxy_property(bool,'IsPrimary',AccessMode.ReadOnly)
    Key: int = proxy_property(int,'Key',AccessMode.ReadOnly)