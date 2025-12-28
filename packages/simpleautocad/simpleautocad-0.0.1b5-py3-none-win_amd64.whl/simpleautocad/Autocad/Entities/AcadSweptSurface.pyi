from ..Base import *
from ..Proxy import *
from .AcadSurface import AcadSurface as AcadSurface

class AcadSweptSurface(AcadSurface):
    def __init__(self, obj) -> None: ...
    Bank: bool
    ProfileRotation: float
    Scale: float
    Twist: float
    def Copy(self) -> AcadSweptSurface: ...
