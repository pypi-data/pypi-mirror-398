from ..Base import *
from ..Proxy import *
from ..AcadObject import *
from .AcadBlocks import AcadBlocks as AcadBlocks
from .AcadDatabasePreferences import AcadDatabasePreferences as AcadDatabasePreferences
from .AcadDictionaries import AcadDictionaries as AcadDictionaries
from .AcadDimStyles import AcadDimStyles as AcadDimStyles
from .AcadGroups import AcadGroups as AcadGroups
from .AcadLayers import AcadLayers as AcadLayers
from .AcadLayouts import AcadLayouts as AcadLayouts
from .AcadLineTypes import AcadLineTypes as AcadLineTypes
from .AcadMaterials import AcadMaterials as AcadMaterials
from .AcadModelSpace import AcadModelSpace as AcadModelSpace
from .AcadPaperSpace import AcadPaperSpace as AcadPaperSpace
from .AcadPlotConfigurations import AcadPlotConfigurations as AcadPlotConfigurations
from .AcadRegisteredApplications import AcadRegisteredApplications as AcadRegisteredApplications
from .AcadSectionManager import AcadSectionManager as AcadSectionManager
from .AcadSummaryInfo import AcadSummaryInfo as AcadSummaryInfo
from .AcadTextStyles import AcadTextStyles as AcadTextStyles
from .AcadUCSs import AcadUCSs as AcadUCSs
from .AcadViewports import AcadViewports as AcadViewports
from .AcadViews import AcadViews as AcadViews

class AcadDatabase(AppObject):
    def __init__(self, obj) -> None: ...
    Blocks: AcadBlocks
    Dictionaries: AcadDictionaries
    DimStyles: AcadDimStyles
    ElevationModelSpace: float
    ElevationPaperSpace: float
    Groups: AcadGroups
    Layers: AcadLayers
    Layouts: AcadLayouts
    Limits: vDoubleArray
    Linetypes: AcadLineTypes
    Materials: AcadMaterials
    ModelSpace: AcadModelSpace
    PaperSpace: AcadPaperSpace
    PlotConfigurations: AcadPlotConfigurations
    Preferences: AcadDatabasePreferences
    RegisteredApplications: AcadRegisteredApplications
    SectionManager: AcadSectionManager
    SummaryInfo: AcadSummaryInfo
    TextStyles: AcadTextStyles
    UserCoordinateSystems: AcadUCSs
    Viewports: AcadViewports
    Views: AcadViews
    def CopyObjects(self, Objects: vObjectArray, Owner: vObject = None) -> vObjectArray: ...
    def HandleToObject(self, Handle: str) -> AppObject: ...
    def ObjectIdToObject(self, ID: int) -> AppObject: ...

class IAcadDatabase(AcadDatabase):
    def __init__(self, obj) -> None: ...
    Application: AcadApplication
