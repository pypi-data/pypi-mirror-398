from __future__ import annotations
from ..Base import *
from ..Proxy import *
from ..AcadEntity import AcadEntity



class AcadRegion(AcadEntity):
    def __init__(self, obj) -> None: super().__init__(obj)

    Area: float = proxy_property(float,'Area',AccessMode.ReadOnly)
    Centroid: PyGePoint2d = proxy_property('PyGePoint2d','Centroid',AccessMode.ReadOnly)
    MomentOfInertia: PyGePoint3d = proxy_property('PyGePoint3d','MomentOfInertia',AccessMode.ReadOnly)
    Normal: PyGeVector3d = proxy_property('PyGeVector3d','Normal',AccessMode.ReadWrite)
    Perimeter: float = proxy_property(float,'Normal',AccessMode.ReadOnly)
    PrincipalDirections: PyGeVector3d = proxy_property('PyGeVector3d','PrincipalDirections',AccessMode.ReadOnly)
    PrincipalMoments: PyGeVector3d = proxy_property('PyGeVector3d','PrincipalMoments',AccessMode.ReadOnly)
    ProductOfInertia: PyGeVector3d = proxy_property('PyGeVector3d','ProductOfInertia',AccessMode.ReadOnly)
    RadiiOfGyration: PyGeVector3d = proxy_property('PyGeVector3d','RadiiOfGyration',AccessMode.ReadOnly)

    def Boolean(self, Operation: AcBooleanType, Object: Acad3DSolid | AcadRegion ) -> None:
        self._obj.Boolean(Operation.value, Object())
        
    def Copy(self) -> AcadRegion:
        return AcadRegion(self._obj.Copy())
        
    def Explode(self) -> vObjectArray:
        return vObjectArray(self._obj.Explode())