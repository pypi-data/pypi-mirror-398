from __future__ import annotations
from ..Base import *
from ..Proxy import *
from ..AcadObject import *
from .AcadBlocks import AcadBlocks
from .AcadDictionaries import AcadDictionaries
from .AcadDimStyles import AcadDimStyles
from .AcadGroups import AcadGroups
from .AcadLayers import AcadLayers
from .AcadLayouts import AcadLayouts
from .AcadLineTypes import AcadLineTypes
from .AcadMaterials import AcadMaterials
from .AcadModelSpace import AcadModelSpace
from .AcadPaperSpace import AcadPaperSpace
from .AcadPlotConfigurations import AcadPlotConfigurations
from .AcadDatabasePreferences import AcadDatabasePreferences
from .AcadRegisteredApplications import AcadRegisteredApplications
from .AcadSectionManager import AcadSectionManager
from .AcadSummaryInfo import AcadSummaryInfo
from .AcadTextStyles import AcadTextStyles
from .AcadUCSs import AcadUCSs
from .AcadViewports import AcadViewports
from .AcadViews import AcadViews




class AcadDatabase(AppObject):
    def __init__(self, obj) -> None: super().__init__(obj)

    Blocks: AcadBlocks = proxy_property('AcadBlocks','Blocks',AccessMode.ReadOnly)
    Dictionaries: AcadDictionaries = proxy_property('AcadDictionaries','Dictionaries',AccessMode.ReadOnly)
    DimStyles: AcadDimStyles = proxy_property('AcadDimStyles','DimStyles',AccessMode.ReadOnly)
    ElevationModelSpace: float = proxy_property(float,'ElevationModelSpace',AccessMode.ReadWrite)
    ElevationPaperSpace: float = proxy_property(float,'ElevationPaperSpace',AccessMode.ReadWrite)
    Groups: AcadGroups = proxy_property('AcadGroups','Groups',AccessMode.ReadOnly)
    Layers: AcadLayers = proxy_property('AcadLayers','Layers',AccessMode.ReadOnly)
    Layouts: AcadLayouts = proxy_property('AcadLayouts','Layouts',AccessMode.ReadOnly)
    Limits: vDoubleArray = proxy_property('vDoubleArray','Limits',AccessMode.ReadWrite)
    Linetypes: AcadLineTypes = proxy_property('AcadLineTypes','Linetypes',AccessMode.ReadOnly)
    Materials: AcadMaterials = proxy_property('AcadMaterials','Materials',AccessMode.ReadOnly)
    ModelSpace: AcadModelSpace = proxy_property('AcadModelSpace','ModelSpace',AccessMode.ReadOnly)
    PaperSpace: AcadPaperSpace = proxy_property('AcadPaperSpace','PaperSpace',AccessMode.ReadOnly)
    PlotConfigurations: AcadPlotConfigurations = proxy_property('AcadPlotConfigurations','PlotConfigurations',AccessMode.ReadOnly)
    Preferences: AcadDatabasePreferences = proxy_property('AcadDatabasePreferences','Preferences',AccessMode.ReadOnly)
    RegisteredApplications: AcadRegisteredApplications = proxy_property('AcadRegisteredApplications','RegisteredApplications',AccessMode.ReadOnly)
    SectionManager: AcadSectionManager = proxy_property('AcadSectionManager','SectionManager',AccessMode.ReadOnly)
    SummaryInfo: AcadSummaryInfo = proxy_property('AcadSummaryInfo','SummaryInfo',AccessMode.ReadOnly)
    TextStyles: AcadTextStyles = proxy_property('AcadTextStyles','TextStyles',AccessMode.ReadOnly)
    UserCoordinateSystems: AcadUCSs = proxy_property('AcadUCSs','UserCoordinateSystems',AccessMode.ReadOnly)
    Viewports: AcadViewports = proxy_property('AcadViewports','Viewports',AccessMode.ReadOnly)
    Views: AcadViews = proxy_property('AcadViews','Views',AccessMode.ReadOnly)

    def CopyObjects(self, Objects: vObjectArray, Owner: vObject = None) -> vObjectArray: #AcadIDPair
        IDPairs = vObjectEmpty
        return vObjectArray(self._obj.CopyObjects(Objects, Owner(), IDPairs()))

    def HandleToObject(self, Handle: str) -> AppObject: 
        return AppObject(self._obj.HandleToObject(Handle))

    def ObjectIdToObject(self, ID: int) -> AppObject: 
        return AppObject(self._obj.ObjectIDToObject(ID))
 
class IAcadDatabase(AcadDatabase):
    def __init__(self, obj) -> None: super().__init__(obj)

    Application: AcadApplication = proxy_property('AcadApplication','Application',AccessMode.ReadOnly)
