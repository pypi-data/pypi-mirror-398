from __future__ import annotations
from ..Base import *
from ..Proxy import *
from ..AcadObject import *

class AcadSubEntity(AppObject):
    def __init__(self, obj) -> None: super().__init__(obj)
    
    Color: AcColor = proxy_property('AcColor','Color',AccessMode.ReadWrite)
    Hyperlinks: AcadHyperlinks = proxy_property('AcadHyperlinks','Hyperlinks',AccessMode.ReadOnly)
    Layer: str = proxy_property(str,'Layer',AccessMode.ReadWrite)
    Linetype: str = proxy_property(str,'Linetype',AccessMode.ReadWrite)
    LinetypeScale: float = proxy_property(float,'LinetypeScale',AccessMode.ReadWrite)
    Lineweight: AcLineWeight = proxy_property('AcLineWeight','Lineweight',AccessMode.ReadWrite)
    ObjectName: str = proxy_property(str,'ObjectName',AccessMode.ReadOnly)
    PlotStyleName: str = proxy_property(str,'PlotStyleName',AccessMode.ReadWrite)
