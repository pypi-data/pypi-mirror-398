from ..Base import *
from ..Proxy import *
from ..AcadObject import *
from .AcadBlock import IAcadBlock as IAcadBlock

class AcadPaperSpace(IAcadBlock):
    def __init__(self, obj) -> None: ...
    Name: str
    def AddPViewport(self, Center: PyGePoint3d, Width: float, Height: float) -> AcadPViewport: ...
