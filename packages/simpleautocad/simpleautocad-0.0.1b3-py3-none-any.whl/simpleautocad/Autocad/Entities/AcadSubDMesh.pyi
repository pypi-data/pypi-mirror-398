from ..Base import *
from ..Proxy import *
from ..AcadEntity import AcadEntity as AcadEntity

class AcadSubDMesh(AcadEntity):
    def __init__(self, obj) -> None: ...
    Coordinates: PyGePoint3dArray
    NumberOfFaces: int
    NumberOfVertices: int
    def Coordinate(self, Index: int) -> PyGePoint3d: ...
    def Copy(self) -> AcadPolyfaceMesh: ...
