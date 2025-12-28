from ..Base import *
from ..Proxy import *
from ..AcadEntity import AcadEntity as AcadEntity

class AcadRegion(AcadEntity):
    def __init__(self, obj) -> None: ...
    Area: float
    Centroid: PyGePoint2d
    MomentOfInertia: PyGePoint3d
    Normal: PyGeVector3d
    Perimeter: float
    PrincipalDirections: PyGeVector3d
    PrincipalMoments: PyGeVector3d
    ProductOfInertia: PyGeVector3d
    RadiiOfGyration: PyGeVector3d
    def Boolean(self, Operation: AcBooleanType, Object: Acad3DSolid | AcadRegion) -> None: ...
    def Copy(self) -> AcadRegion: ...
    def Explode(self) -> vObjectArray: ...
