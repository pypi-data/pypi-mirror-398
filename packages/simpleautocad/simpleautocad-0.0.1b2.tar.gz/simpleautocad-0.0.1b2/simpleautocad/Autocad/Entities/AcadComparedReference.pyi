from ..Base import *
from ..Proxy import *
from .AcadExternalReference import AcadExternalReference as AcadExternalReference

class AcadComparedReference(AcadExternalReference):
    def __init__(self, obj) -> None: ...
    def Copy(self) -> AcadComparedReference: ...
