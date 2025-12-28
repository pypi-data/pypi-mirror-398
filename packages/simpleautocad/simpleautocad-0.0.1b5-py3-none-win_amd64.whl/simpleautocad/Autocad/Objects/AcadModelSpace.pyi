from ..Base import *
from ..Proxy import *
from ..AcadObject import *
from .AcadBlock import IAcadBlock as IAcadBlock

class AcadModelSpace(IAcadBlock):
    def __init__(self, obj) -> None: ...
    Comments: str
    Layout: AcadLayout
    Name: str
    Origin: PyGePoint3d
    Units: AcInsertUnits
