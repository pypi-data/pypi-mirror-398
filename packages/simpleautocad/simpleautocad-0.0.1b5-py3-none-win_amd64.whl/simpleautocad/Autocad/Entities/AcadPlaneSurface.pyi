from ..Base import *
from ..Proxy import *
from .AcadSurface import AcadSurface as AcadSurface

class AcadPlaneSurface(AcadSurface):
    def __init__(self, obj) -> None: ...
    def Copy(self) -> AcadPlaneSurface: ...
