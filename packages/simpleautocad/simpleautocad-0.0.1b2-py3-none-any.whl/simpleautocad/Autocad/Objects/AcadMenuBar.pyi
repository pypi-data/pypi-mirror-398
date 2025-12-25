from ..Base import *
from ..Proxy import *
from ..Objects.AcadApplication import AcadApplication as AcadApplication

class AcadMenuBar(AppObjectCollection):
    def __init__(self, obj) -> None: ...
    Application: AcadApplication
    Count: int
    Parent: AppObject
