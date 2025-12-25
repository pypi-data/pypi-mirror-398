from ..Base import *
from ..Proxy import *
from ..AcadObject import AcadObject as AcadObject

class AcadUCS(AcadObject):
    def __init__(self, obj) -> None: ...
    Name: str
    Origin: PyGePoint3d
    XVector: PyGeVector3d
    YVector: PyGeVector3d
    def GetUCSMatrix(self) -> vDoubleArray: ...
