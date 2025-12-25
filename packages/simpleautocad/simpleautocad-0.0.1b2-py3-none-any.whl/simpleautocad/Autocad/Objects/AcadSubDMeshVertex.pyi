from ..Base import *
from ..Proxy import *
from .AcadSubEntity import *

class AcadSubDMeshVertex(AcadSubEntity):
    def __init__(self, obj) -> None: ...
    Coordinates: PyGePoint3dArray
    CreaseLevel: float
    CreaseType: AcMeshCreaseType
