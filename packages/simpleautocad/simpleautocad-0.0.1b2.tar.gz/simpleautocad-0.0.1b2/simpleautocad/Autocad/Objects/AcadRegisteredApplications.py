from __future__ import annotations
# from ..Base import *
# from ..Proxy import proxy_property, AccessMode
from ..AcadObject import *
from .AcadRegisteredApplication import AcadRegisteredApplication



class AcadRegisteredApplications(IAcadObjectCollection):
    def __init__(self, obj) -> None: super().__init__(obj)

    def Add(self, Name: str) -> AcadRegisteredApplication:
        return AcadRegisteredApplication(self._obj.Add(Name))

    def Item(self, Index: int) -> AcadRegisteredApplication:
        return AcadRegisteredApplication(self._obj.Item(Index))

    def __iter__(self):
        for item in self._obj:
            obj = AcadRegisteredApplication(item)
            yield obj
