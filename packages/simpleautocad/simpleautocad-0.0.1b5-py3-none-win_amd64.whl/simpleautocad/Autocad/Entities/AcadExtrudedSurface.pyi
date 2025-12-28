from ..Base import *
from ..Proxy import *
from .AcadSurface import AcadSurface as AcadSurface

class AcadExtrudedSurface(AcadSurface):
    def __init__(self, obj) -> None: ...
    Direction: PyGeVector3d
    Height: float
    TaperAngle: float
    def Copy(self) -> AcadExtrudedSurface: ...
