from ..Base import *
from ..Proxy import *
from .AcadSurface import AcadSurface as AcadSurface

class AcadNurbSurface(AcadSurface):
    def __init__(self, obj) -> None: ...
    CvHullDisplay: bool
    Height: float
    def Copy(self) -> AcadNurbSurface: ...
