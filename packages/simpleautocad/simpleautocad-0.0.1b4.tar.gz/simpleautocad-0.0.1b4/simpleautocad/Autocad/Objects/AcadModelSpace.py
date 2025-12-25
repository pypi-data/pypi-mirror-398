from __future__ import annotations
from ..Base import *
from ..Proxy import *
from ..AcadObject import *
from .AcadBlock import IAcadBlock


class AcadModelSpace(IAcadBlock):
    def __init__(self, obj) -> None: super().__init__(obj)

    Comments: str = proxy_property(str,'Comments',AccessMode.ReadWrite)
    Layout: AcadLayout = proxy_property('AcadLayout','Layout',AccessMode.ReadWrite)
    Name: str = proxy_property(str,'Name',AccessMode.ReadOnly)
    Origin: PyGePoint3d = proxy_property('PyGePoint3d','Origin',AccessMode.ReadWrite)
    Units: AcInsertUnits = proxy_property('AcInsertUnits','Units',AccessMode.ReadWrite)
