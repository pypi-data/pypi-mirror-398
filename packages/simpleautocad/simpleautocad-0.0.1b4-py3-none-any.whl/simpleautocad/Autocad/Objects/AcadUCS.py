from __future__ import annotations
from ..Base import *
from ..Proxy import *
from ..AcadObject import AcadObject



class AcadUCS(AcadObject):
    def __init__(self, obj) -> None: super().__init__(obj)

    Name: str = proxy_property(str,'Name',AccessMode.ReadWrite)
    Origin: PyGePoint3d = proxy_property('PyGePoint3d','Origin',AccessMode.ReadWrite)
    XVector: PyGeVector3d = proxy_property('PyGeVector3d','XVector',AccessMode.ReadWrite)
    YVector: PyGeVector3d = proxy_property('PyGeVector3d','YVector',AccessMode.ReadWrite)
        
    def GetUCSMatrix(self) -> vDoubleArray: 
        return vDoubleArray(self._obj.GetUCSMatrix())
