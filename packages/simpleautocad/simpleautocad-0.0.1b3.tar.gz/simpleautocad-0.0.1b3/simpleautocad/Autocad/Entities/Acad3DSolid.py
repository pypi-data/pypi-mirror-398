from __future__ import annotations
from ..Base import *
from ..Proxy import *
from ..AcadEntity import AcadEntity



class Acad3DSolid(AcadEntity):
    def __init__(self, obj) -> None: super().__init__(obj)

    Centroid: PyGePoint2d = proxy_property('PyGePoint2d','Centroid',AccessMode.ReadOnly)
    History: bool = proxy_property(bool,'History',AccessMode.ReadWrite)
    MomentOfInertia: PyGePoint3d = proxy_property('PyGePoint3d','MomentOfInertia',AccessMode.ReadOnly)
    Position: PyGePoint3d = proxy_property('PyGePoint3d','Position',AccessMode.ReadOnly)
    PrincipalDirections: PyGeVector3d = proxy_property('PyGeVector3d','PrincipalDirections',AccessMode.ReadOnly)
    PrincipalMoments: PyGeVector3d = proxy_property('PyGeVector3d','PrincipalMoments',AccessMode.ReadOnly)
    ProductOfInertia: PyGeVector3d = proxy_property('PyGeVector3d','ProductOfInertia',AccessMode.ReadOnly)
    RadiiOfGyration: PyGeVector3d = proxy_property('PyGeVector3d','RadiiOfGyration',AccessMode.ReadOnly)
    ShowHistory: bool = proxy_property(bool,'ShowHistory',AccessMode.ReadWrite)
    SolidType: str = proxy_property(str,'SolidType',AccessMode.ReadWrite)
    Volume: float = proxy_property(float,'Volume',AccessMode.ReadOnly)
    
    def Boolean(self, Operation: AcBooleanType, Object: Acad3DSolid | AcadRegion) -> None:
        self._obj.Boolean(Operation.value, Object())
        
    def CheckInterference(self, Object: Acad3DSolid, CreateInterferenceSolid: bool) -> bool:
        SolidsInterfere = self._obj.CheckInterference(Object(), CreateInterferenceSolid)
        return SolidsInterfere

    def Delete(self) -> None:
        self._obj.Delete()

    def Copy(self) -> Acad3DSolid:
        return Acad3DSolid(self._obj.Copy())
        
    def SectionSolid(self, Point1: PyGePoint3d, Point2: PyGePoint3d, Point3: PyGePoint3d) -> AcadRegion:
        return AcadRegion(self._obj.SectionSolid(Point1(), Point2(), Point3()))

    def SliceSolid(self, Point1: PyGePoint3d, Point2: PyGePoint3d, Point3: PyGePoint3d, Negative: bool) -> Acad3DSolid:
        return Acad3DSolid(self._obj.SliceSolid(Point1(), Point2(), Point3(), Negative))
