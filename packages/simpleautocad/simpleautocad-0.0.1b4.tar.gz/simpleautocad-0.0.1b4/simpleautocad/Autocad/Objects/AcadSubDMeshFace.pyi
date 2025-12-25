from ..Base import *
from ..Proxy import *
from .AcadSubEntity import *

class AcadSubDMeshFace(AcadSubEntity):
    def __init__(self, obj) -> None: ...
    CreaseLevel: float
    CreaseType: AcMeshCreaseType
    Material: str
