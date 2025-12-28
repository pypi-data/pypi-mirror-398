from ..Base import *
from ..Proxy import *
from ..AcadObject import *

class AcadSubEntity(AppObject):
    def __init__(self, obj) -> None: ...
    Color: AcColor
    Hyperlinks: AcadHyperlinks
    Layer: str
    Linetype: str
    LinetypeScale: float
    Lineweight: AcLineWeight
    ObjectName: str
    PlotStyleName: str
