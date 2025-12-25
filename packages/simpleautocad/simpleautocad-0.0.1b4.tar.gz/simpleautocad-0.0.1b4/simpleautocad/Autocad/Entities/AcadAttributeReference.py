from __future__ import annotations
from ..Base import *
from ..Proxy import *
from ..AcadEntity import AcadEntity



class AcadAttributeReference(AcadEntity):
    def __init__(self, obj) -> None: super().__init__(obj)

    Alignment: AcAlignment = proxy_property('AcAlignment','Alignment',AccessMode.ReadWrite)
    Backward: bool = proxy_property(bool,'Backward',AccessMode.ReadWrite)
    Constant: bool = proxy_property(bool,'Constant',AccessMode.ReadOnly)
    FieldLength: int = proxy_property(int,'FieldLength',AccessMode.ReadWrite)
    Height: float = proxy_property(float,'Height',AccessMode.ReadWrite)
    InsertionPoint: PyGePoint3d = proxy_property('PyGePoint3d','InsertionPoint',AccessMode.ReadWrite)
    Invisible: bool = proxy_property(bool,'InsertionPoint',AccessMode.ReadWrite)
    LockPosition: bool = proxy_property(bool,'LockPosition',AccessMode.ReadOnly)
    MTextAttribute: bool = proxy_property(bool,'MTextAttribute',AccessMode.ReadWrite)
    MTextAttributeContent: str = proxy_property(str,'MTextAttributeContent',AccessMode.ReadWrite)
    MTextBoundaryWidth: float = proxy_property(float,'MTextBoundaryWidth',AccessMode.ReadWrite)
    MTextDrawingDirection: AcDrawingDirection = proxy_property('AcDrawingDirection' ,'MTextDrawingDirection',AccessMode.ReadWrite)
    Normal: PyGeVector3d = proxy_property('PyGeVector3d','Normal',AccessMode.ReadWrite)
    ObliqueAngle: float = proxy_property(float,'ObliqueAngle',AccessMode.ReadWrite)
    Rotation: float = proxy_property(float,'Rotation',AccessMode.ReadWrite)
    ScaleFactor: float = proxy_property(float,'ScaleFactor',AccessMode.ReadWrite)
    StyleName: str = proxy_property(str,'StyleName',AccessMode.ReadWrite)
    TagString: str = proxy_property(str,'TagString',AccessMode.ReadWrite)
    TextAlignmentPoint: PyGePoint3d = proxy_property('PyGePoint3d','TextAlignmentPoint',AccessMode.ReadWrite)
    TextGenerationFlag: AcTextGenerationFlag = proxy_property('AcTextGenerationFlag','TextGenerationFlag',AccessMode.ReadWrite)
    TextString: str = proxy_property(str,'TextString',AccessMode.ReadWrite)
    Thickness: float = proxy_property(float,'Thickness',AccessMode.ReadWrite)
    UpsideDown: bool = proxy_property(bool,'UpsideDown',AccessMode.ReadWrite)

    def Copy(self) -> AcadAttributeReference:
        return AcadAttributeReference(self._obj.Copy())

    def UpdateMTextAttribute(self) -> None:
        self._obj.UpdateMTextAttribute()
