from __future__ import annotations
from ..Base import *
from ..Proxy import *
from ..Objects.AcadApplication import AcadApplication


class AcadMenuBar(AppObjectCollection):
    def __init__(self, obj) -> None: super().__init__(obj)

    Application: AcadApplication = proxy_property('AcadApplication','Application',AccessMode.ReadOnly)
    Count: int = proxy_property(int,'Count',AccessMode.ReadOnly)
    Parent: AppObject = proxy_property('AppObject','Parent',AccessMode.ReadWrite)

