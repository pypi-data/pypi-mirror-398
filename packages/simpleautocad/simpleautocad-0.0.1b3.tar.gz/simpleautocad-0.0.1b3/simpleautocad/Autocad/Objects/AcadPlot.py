from __future__ import annotations
from ..Base import *
from ..Proxy import *
from ..AcadObject import *

class AcadPlot(AppObject):
    def __init__(self, obj) -> None: super().__init__(obj)

    Application: AcadApplication = proxy_property('AcadApplication','Application',AccessMode.ReadOnly)
    BatchPlotProgress: bool = proxy_property(bool,'BatchPlotProgress',AccessMode.ReadWrite)
    NumberOfCopies: int = proxy_property(int,'NumberOfCopies',AccessMode.ReadWrite)
    QuietErrorMode: bool = proxy_property(bool,'QuietErrorMode',AccessMode.ReadWrite)


    def DisplayPlotPreview(self, Preview: AcPreviewMode) -> None: 
        self._obj.DisplayPlotPreview(Preview)

    def PlotToDevice(self, plotConfig: str = '') -> bool: 
        return self._obj.PlotToDevice(plotConfig)

    def PlotToFile(self, plotFile: str, plotConfig: str = '') -> bool: 
        return self._obj.PlotToFile(plotFile, plotConfig)

    def SetLayoutsToPlot(self, layoutList: vStringArray) -> None: 
        self._obj.SetLayoutsToPlot(layoutList)
    
    def StartBatchMode(self, entryCount: int) -> None: 
        self._obj.StartBatchMode(entryCount)
