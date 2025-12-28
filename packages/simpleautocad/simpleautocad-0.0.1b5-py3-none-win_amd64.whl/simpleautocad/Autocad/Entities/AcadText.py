from __future__ import annotations
from ..Base import *
from ..Proxy import *
from ..AcadEntity import AcadEntity



class AcadText(AcadEntity):
    def __init__(self, obj) -> None: super().__init__(obj)

    Alignment: AcAlignment = proxy_property('AcAlignment','Alignment',AccessMode.ReadWrite)
    Backward: bool = proxy_property(bool,'Backward',AccessMode.ReadWrite)
    Height: float = proxy_property(float,'Height',AccessMode.ReadWrite)
    InsertionPoint: PyGePoint3d = proxy_property('PyGePoint3d','InsertionPoint',AccessMode.ReadWrite)

    Normal: PyGeVector3d = proxy_property('PyGeVector3d','Normal',AccessMode.ReadWrite)
    ObliqueAngle: float = proxy_property(float,'ObliqueAngle',AccessMode.ReadWrite)
    TextAlignmentPoint: PyGePoint3d = proxy_property('PyGePoint3d','TextAlignmentPoint',AccessMode.ReadWrite)
    TextGenerationFlag: AcTextGenerationFlag = proxy_property('AcTextGenerationFlag','TextGenerationFlag',AccessMode.ReadWrite)
    TextString: str = proxy_property(str,'TextString',AccessMode.ReadWrite)
    Thickness: float = proxy_property(float,'Thickness',AccessMode.ReadWrite)
    UpsideDown: bool = proxy_property(bool,'UpsideDown',AccessMode.ReadWrite)

    def Copy(self) -> AcadText:
        return AcadText(self._obj.Copy())
    
    def FieldCode(self) -> str:
        return self._obj.FieldCode()
