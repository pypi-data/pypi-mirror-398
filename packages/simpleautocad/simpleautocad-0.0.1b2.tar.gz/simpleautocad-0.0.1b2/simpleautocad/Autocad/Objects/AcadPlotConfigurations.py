from __future__ import annotations
from ..Base import *
from ..Proxy import *
from ..AcadObject import *
from .AcadPlotConfiguration import *



class AcadPlotConfigurations(IAcadObjectCollection):
    def __init__(self, obj) -> None: super().__init__(obj)

    def Add(self, Name: str, ModelType: bool = None) -> AcadPlotConfiguration:
        if ModelType is not None:
            return self._obj.Add(Name, ModelType)
        else:
            return self._obj.Add(Name)

    def Item(self, Index: int | str) -> AcadPlotConfiguration:
        return AcadPlotConfiguration(self._obj.Item(Index))

    def __iter__(self):
        for item in self._obj:
            obj = AcadPlotConfiguration(item)
            yield obj