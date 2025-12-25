from ..Base import *
from ..Proxy import *
from .AcadBlockReference import AcadBlockReference as AcadBlockReference

class AcadExternalReference(AcadBlockReference):
    def __init__(self, obj) -> None: ...
    LayerPropertyOverrides: bool
    Path: str
    def Copy(self) -> AcadExternalReference: ...
