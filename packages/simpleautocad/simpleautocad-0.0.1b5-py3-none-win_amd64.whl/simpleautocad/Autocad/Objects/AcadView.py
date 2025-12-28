from __future__ import annotations
from ..Base import *
from ..Proxy import *
from ..AcadObject import *



class AcadView(AcadObject):
    def __init__(self, obj) -> None: super().__init__(obj)

    CategoryName: str = proxy_property(str,'CategoryName',AccessMode.ReadWrite)
    Center: PyGePoint2d = proxy_property('PyGePoint2d','Center',AccessMode.ReadWrite)
    Direction: PyGeVector3d = proxy_property('PyGeVector3d','Direction',AccessMode.ReadWrite)
    HasVpAssociation: bool = proxy_property(bool,'HasVpAssociation',AccessMode.ReadWrite)
    Height: float = proxy_property(float,'Height',AccessMode.ReadWrite)
    LayerState: str = proxy_property(str,'LayerState',AccessMode.ReadWrite)
    LayoutID: int = proxy_property(int,'LayoutID',AccessMode.ReadOnly)
    Name: str = proxy_property(str,'Name',AccessMode.ReadWrite)
    Target: PyGePoint3d = proxy_property('PyGePoint3d','Target',AccessMode.ReadWrite)
    Width: float = proxy_property(float,'Width',AccessMode.ReadWrite)
