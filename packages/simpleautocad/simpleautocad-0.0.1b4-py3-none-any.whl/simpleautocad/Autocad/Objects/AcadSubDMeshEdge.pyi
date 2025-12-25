from ..Base import *
from ..Proxy import *
from .AcadSubEntity import *

class AcadSubDMeshEdge(AcadSubEntity):
    def __init__(self, obj) -> None: ...
    CreaseLevel: float
    CreaseType: AcMeshCreaseType
