from __future__ import annotations
from ..Base import *
from ..Proxy import *
from ..AcadEntity import AcadEntity



class AcadMtext(AcadEntity):
    def __init__(self, obj) -> None: super().__init__(obj)

    AttachmentPoint: AcAttachmentPoint = proxy_property('AcAttachmentPoint','AttachmentPoint',AccessMode.ReadWrite)
    BackgroundFill: bool = proxy_property(bool,'BackgroundFill',AccessMode.ReadWrite)
    DrawingDirection: AcDrawingDirection = proxy_property('AcDrawingDirection','DrawingDirection',AccessMode.ReadWrite)
    Height: float = proxy_property(float,'Height',AccessMode.ReadWrite)
    InsertionPoint: PyGePoint3d = proxy_property('PyGePoint3d','InsertionPoint',AccessMode.ReadWrite)
    LineSpacingDistance: float = proxy_property(float,'LineSpacingDistance',AccessMode.ReadWrite)
    LineSpacingFactor: float = proxy_property(float,'LineSpacingFactor',AccessMode.ReadWrite)
    LineSpacingStyle: AcLineSpacingStyle = proxy_property('AcLineSpacingStyle','LineSpacingStyle',AccessMode.ReadWrite)
    Normal: PyGeVector3d = proxy_property('PyGeVector3d','Normal',AccessMode.ReadWrite)
    TextString: str = proxy_property(str,'TextString',AccessMode.ReadWrite)
    Width: float = proxy_property(float,'TextString',AccessMode.ReadWrite)

    def FieldCode(self) -> str:
        return self._obj.FieldCode()

    def Copy(self) -> AcadMtext:
        return AcadMtext(self._obj.Copy())
