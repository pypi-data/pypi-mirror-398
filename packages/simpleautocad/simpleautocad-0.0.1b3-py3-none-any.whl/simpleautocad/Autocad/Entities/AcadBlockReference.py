from __future__ import annotations
from ..Base import *
from ..Proxy import *
from ..AcadEntity import AcadEntity



class AcadBlockReference(AcadEntity):
    def __init__(self, obj) -> None: super().__init__(obj)

    EffectiveName: str = proxy_property(str,'EffectiveName',AccessMode.ReadOnly)
    HasAttributes: bool = proxy_property(bool,'EffectiveName',AccessMode.ReadOnly)
    InsertionPoint: PyGePoint3d = proxy_property('PyGePoint3d','InsertionPoint',AccessMode.ReadWrite)
    InsUnits: str = proxy_property(str,'InsUnits',AccessMode.ReadOnly)
    InsUnitsFactor: float = proxy_property(float,'InsUnitsFactor',AccessMode.ReadOnly)
    IsDynamicBlock: bool = proxy_property(bool,'IsDynamicBlock',AccessMode.ReadOnly)
    Name: bool = proxy_property(bool,'Name',AccessMode.ReadWrite)
    Normal: PyGeVector3d = proxy_property('PyGeVector3d','Normal',AccessMode.ReadWrite)
    Rotation: float = proxy_property(float,'Rotation',AccessMode.ReadWrite)
    XEffectiveScaleFactor: float = proxy_property(float,'XEffectiveScaleFactor',AccessMode.ReadWrite)
    XScaleFactor: float = proxy_property(float,'XScaleFactor',AccessMode.ReadWrite)
    YEffectiveScaleFactor: float = proxy_property(float,'YEffectiveScaleFactor',AccessMode.ReadWrite)
    YScaleFactor: float = proxy_property(float,'YScaleFactor',AccessMode.ReadWrite)
    ZEffectiveScaleFactor: float = proxy_property(float,'ZEffectiveScaleFactor',AccessMode.ReadWrite)
    ZScaleFactor: float = proxy_property(float,'ZEffectiveScaleFactor',AccessMode.ReadWrite)

    def ConvertToAnonymousBlock(self) -> None:
        self._obj.ConvertToAnonymousBlock()

    def ConvertToStaticBlock(self, newBlockName: str) -> None:
        self._obj.ConvertToStaticBlock(newBlockName)

    def Copy(self) -> AcadBlockReference:
        return AcadBlockReference(self._obj.Copy())
        
    def Explode(self) -> vObjectArray:
        return vObjectArray(self._obj.Explode())
        
    def GetAttributes(self) -> vObjectArray[AcadAttributeReference]:
        return vObjectArray(self._obj.GetAttributes())
            
    def GetConstantAttributes(self) -> vObjectArray[AcadAttribute]:
        return vObjectArray(self._obj.GetConstantAttributes())
        
    def GetDynamicBlockProperties(self) -> vObjectArray[AcadDynamicBlockReferenceProperty]:
        return vObjectArray(self._obj.GetDynamicBlockProperties())
        
    def ResetBlock(self) -> None:
        self._obj.ResetBlock()