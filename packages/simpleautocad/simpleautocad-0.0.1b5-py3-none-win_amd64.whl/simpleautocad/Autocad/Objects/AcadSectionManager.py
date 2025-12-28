from __future__ import annotations
from ..Base import *
from ..Proxy import *
from ..AcadObject import *



class AcadSectionManager(IAcadObjectCollection):
    def __init__(self, obj) -> None: super().__init__(obj)

    def GetLiveSection(self) -> AcadSection:
        return AcadSection(self._obj.GetLiveSection())

    def GetUniqueSectionName(self) -> str:
        return self._obj.GetUniqueSectionName()
