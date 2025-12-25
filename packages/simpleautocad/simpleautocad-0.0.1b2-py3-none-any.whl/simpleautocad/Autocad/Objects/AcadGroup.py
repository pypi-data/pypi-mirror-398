from __future__ import annotations
from ..Base import *
from ..Proxy import proxy_property, AccessMode
from ..AcadObject import *



class AcadGroup(IAcadObjectCollection):
    def __init__(self, obj) -> None: super().__init__(obj)

    Layer: str = proxy_property(str,'Layer',AccessMode.WriteOnly) #Group object which is write-only
    Linetype: str = proxy_property(str,'Linetype',AccessMode.WriteOnly) #Group object which is write-only
    LinetypeScale: float = proxy_property(float,'LinetypeScale',AccessMode.WriteOnly) #Group object which is write-only
    Lineweight: AcLineWeight = proxy_property('AcLineWeight','Lineweight',AccessMode.ReadWrite)
    Material: str = proxy_property(str,'Material',AccessMode.ReadWrite)
    Name: str = proxy_property(str,'Name',AccessMode.ReadWrite)
    PlotStyleName: str = proxy_property(str,'PlotStyleName',AccessMode.WriteOnly) #Group object which is write-only
    TrueColor: AcadAcCmColor = proxy_property('AcadAcCmColor','TrueColor',AccessMode.WriteOnly) #Group object which is write-only
    Visible: bool = proxy_property(bool,'Visible',AccessMode.WriteOnly) #Group object which is write-only

    def AppendItems(self, Objects: vObjectArray) -> None: 
        self._obj.AppendItems(Objects())

    def Highlight(self, HighlightFlag: bool) -> None: 
        self._obj.Highlight(HighlightFlag)

    def RemoveItems(self, Objects: vObjectArray) -> None:
        self._obj.RemoveItems(Objects())

    def Update(self) -> None:
        self._obj.Update()
