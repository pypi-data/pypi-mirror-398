from __future__ import annotations
from ..Base import *
from ..Proxy import *
from ..AcadObject import *



class AcadSectionSettings(AcadObject):
    def __init__(self, obj) -> None: super().__init__(obj)

    CurrentSectionType: AcSectionType = proxy_property('AcSectionType','CurrentSectionType',AccessMode.ReadWrite)
