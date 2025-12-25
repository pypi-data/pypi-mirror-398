from ..Types import *
from .Base import *
from .Entities.Acad3DFace import Acad3DFace as Acad3DFace
from .Entities.Acad3DPolyline import Acad3DPolyline as Acad3DPolyline
from .Entities.Acad3DSolid import Acad3DSolid as Acad3DSolid
from .Entities.AcadArc import AcadArc as AcadArc
from .Entities.AcadAttribute import AcadAttribute as AcadAttribute
from .Entities.AcadAttributeReference import AcadAttributeReference as AcadAttributeReference
from .Entities.AcadBlockReference import AcadBlockReference as AcadBlockReference
from .Entities.AcadCircle import AcadCircle as AcadCircle
from .Entities.AcadComparedReference import AcadComparedReference as AcadComparedReference
from .Entities.AcadDgnUnderlay import AcadDgnUnderlay as AcadDgnUnderlay
from .Entities.AcadDim3PointAngular import AcadDim3PointAngular as AcadDim3PointAngular
from .Entities.AcadDimAligned import AcadDimAligned as AcadDimAligned
from .Entities.AcadDimAngular import AcadDimAngular as AcadDimAngular
from .Entities.AcadDimArcLength import AcadDimArcLength as AcadDimArcLength
from .Entities.AcadDimDiametric import AcadDimDiametric as AcadDimDiametric
from .Entities.AcadDimOrdinate import AcadDimOrdinate as AcadDimOrdinate
from .Entities.AcadDimRadial import AcadDimRadial as AcadDimRadial
from .Entities.AcadDimRadialLarge import AcadDimRadialLarge as AcadDimRadialLarge
from .Entities.AcadDimRotated import AcadDimRotated as AcadDimRotated
from .Entities.AcadDimension import AcadDimension as AcadDimension
from .Entities.AcadDwfUnderlay import AcadDwfUnderlay as AcadDwfUnderlay
from .Entities.AcadEllipse import AcadEllipse as AcadEllipse
from .Entities.AcadExternalReference import AcadExternalReference as AcadExternalReference
from .Entities.AcadExtrudedSurface import AcadExtrudedSurface as AcadExtrudedSurface
from .Entities.AcadGeoPositionMarker import AcadGeoPositionMarker as AcadGeoPositionMarker
from .Entities.AcadGeomapImage import AcadGeomapImage as AcadGeomapImage
from .Entities.AcadHatch import AcadHatch as AcadHatch
from .Entities.AcadHelix import AcadHelix as AcadHelix
from .Entities.AcadLWPolyline import AcadLWPolyline as AcadLWPolyline
from .Entities.AcadLeader import AcadLeader as AcadLeader
from .Entities.AcadLine import AcadLine as AcadLine
from .Entities.AcadLoftedSurface import AcadLoftedSurface as AcadLoftedSurface
from .Entities.AcadMInsertBlock import AcadMInsertBlock as AcadMInsertBlock
from .Entities.AcadMLeader import AcadMLeader as AcadMLeader
from .Entities.AcadMLine import AcadMLine as AcadMLine
from .Entities.AcadMtext import AcadMtext as AcadMtext
from .Entities.AcadNurbSurface import AcadNurbSurface as AcadNurbSurface
from .Entities.AcadOle import AcadOle as AcadOle
from .Entities.AcadPViewport import AcadPViewport as AcadPViewport
from .Entities.AcadPdfUnderlay import AcadPdfUnderlay as AcadPdfUnderlay
from .Entities.AcadPlaneSurface import AcadPlaneSurface as AcadPlaneSurface
from .Entities.AcadPoint import AcadPoint as AcadPoint
from .Entities.AcadPointCloud import AcadPointCloud as AcadPointCloud
from .Entities.AcadPointCloudEx import AcadPointCloudEx as AcadPointCloudEx
from .Entities.AcadPolyfaceMesh import AcadPolyfaceMesh as AcadPolyfaceMesh
from .Entities.AcadPolygonMesh import AcadPolygonMesh as AcadPolygonMesh
from .Entities.AcadPolyline import AcadPolyline as AcadPolyline
from .Entities.AcadRasterImage import AcadRasterImage as AcadRasterImage
from .Entities.AcadRay import AcadRay as AcadRay
from .Entities.AcadRegion import AcadRegion as AcadRegion
from .Entities.AcadSection import AcadSection as AcadSection
from .Entities.AcadShape import AcadShape as AcadShape
from .Entities.AcadSolid import AcadSolid as AcadSolid
from .Entities.AcadSpline import AcadSpline as AcadSpline
from .Entities.AcadSubDMesh import AcadSubDMesh as AcadSubDMesh
from .Entities.AcadSurface import AcadSurface as AcadSurface
from .Entities.AcadSweptSurface import AcadSweptSurface as AcadSweptSurface
from .Entities.AcadTable import AcadTable as AcadTable
from .Entities.AcadText import AcadText as AcadText
from .Entities.AcadTolerance import AcadTolerance as AcadTolerance
from .Entities.AcadTrace import AcadTrace as AcadTrace
from .Entities.AcadUnderlay import AcadUnderlay as AcadUnderlay
from .Entities.AcadWipeout import AcadWipeout as AcadWipeout
from .Entities.AcadXline import AcadXline as AcadXline
from .Objects.AcadAcCmColor import AcadAcCmColor as AcadAcCmColor
from .Objects.AcadApplication import AcadApplication as AcadApplication
from .Objects.AcadBlock import AcadBlock as AcadBlock
from .Objects.AcadBlocks import AcadBlocks as AcadBlocks
from .Objects.AcadDatabase import AcadDatabase as AcadDatabase, IAcadDatabase as IAcadDatabase
from .Objects.AcadDatabasePreferences import AcadDatabasePreferences as AcadDatabasePreferences
from .Objects.AcadDictionaries import AcadDictionaries as AcadDictionaries
from .Objects.AcadDictionary import AcadDictionary as AcadDictionary
from .Objects.AcadDimStyle import AcadDimStyle as AcadDimStyle
from .Objects.AcadDimStyles import AcadDimStyles as AcadDimStyles
from .Objects.AcadDocument import AcadDocument as AcadDocument
from .Objects.AcadDocuments import AcadDocuments as AcadDocuments
from .Objects.AcadDynamicBlockReferenceProperty import AcadDynamicBlockReferenceProperty as AcadDynamicBlockReferenceProperty
from .Objects.AcadGroup import AcadGroup as AcadGroup
from .Objects.AcadGroups import AcadGroups as AcadGroups
from .Objects.AcadHyperlink import AcadHyperlink as AcadHyperlink
from .Objects.AcadHyperlinks import AcadHyperlinks as AcadHyperlinks
from .Objects.AcadIDPair import AcadIDPair as AcadIDPair
from .Objects.AcadLayer import AcadLayer as AcadLayer
from .Objects.AcadLayerStateManager import AcadLayerStateManager as AcadLayerStateManager
from .Objects.AcadLayers import AcadLayers as AcadLayers
from .Objects.AcadLayout import AcadLayout as AcadLayout
from .Objects.AcadLayouts import AcadLayouts as AcadLayouts
from .Objects.AcadLineType import AcadLineType as AcadLineType
from .Objects.AcadLineTypes import AcadLineTypes as AcadLineTypes
from .Objects.AcadMLeaderLeader import AcadMLeaderLeader as AcadMLeaderLeader
from .Objects.AcadMLeaderStyle import AcadMLeaderStyle as AcadMLeaderStyle
from .Objects.AcadMaterial import AcadMaterial as AcadMaterial
from .Objects.AcadMaterials import AcadMaterials as AcadMaterials
from .Objects.AcadMenuBar import AcadMenuBar as AcadMenuBar
from .Objects.AcadMenuGroup import AcadMenuGroup as AcadMenuGroup
from .Objects.AcadMenuGroups import AcadMenuGroups as AcadMenuGroups
from .Objects.AcadModelSpace import AcadModelSpace as AcadModelSpace
from .Objects.AcadPaperSpace import AcadPaperSpace as AcadPaperSpace
from .Objects.AcadPlot import AcadPlot as AcadPlot
from .Objects.AcadPlotConfiguration import AcadPlotConfiguration as AcadPlotConfiguration
from .Objects.AcadPlotConfigurations import AcadPlotConfigurations as AcadPlotConfigurations
from .Objects.AcadPopupMenu import AcadPopupMenu as AcadPopupMenu
from .Objects.AcadPopupMenuItem import AcadPopupMenuItem as AcadPopupMenuItem
from .Objects.AcadPopupMenus import AcadPopupMenus as AcadPopupMenus
from .Objects.AcadPreferences import AcadPreferences as AcadPreferences
from .Objects.AcadPreferencesDisplay import AcadPreferencesDisplay as AcadPreferencesDisplay
from .Objects.AcadPreferencesDrafting import AcadPreferencesDrafting as AcadPreferencesDrafting
from .Objects.AcadPreferencesFiles import AcadPreferencesFiles as AcadPreferencesFiles
from .Objects.AcadPreferencesOpenSave import AcadPreferencesOpenSave as AcadPreferencesOpenSave
from .Objects.AcadPreferencesOutput import AcadPreferencesOutput as AcadPreferencesOutput
from .Objects.AcadPreferencesProfiles import AcadPreferencesProfiles as AcadPreferencesProfiles
from .Objects.AcadPreferencesSelection import AcadPreferencesSelection as AcadPreferencesSelection
from .Objects.AcadPreferencesSystem import AcadPreferencesSystem as AcadPreferencesSystem
from .Objects.AcadPreferencesUser import AcadPreferencesUser as AcadPreferencesUser
from .Objects.AcadRegisteredApplication import AcadRegisteredApplication as AcadRegisteredApplication
from .Objects.AcadRegisteredApplications import AcadRegisteredApplications as AcadRegisteredApplications
from .Objects.AcadSectionManager import AcadSectionManager as AcadSectionManager
from .Objects.AcadSectionSettings import AcadSectionSettings as AcadSectionSettings
from .Objects.AcadSectionTypeSettings import AcadSectionTypeSettings as AcadSectionTypeSettings
from .Objects.AcadSecurityParams import AcadSecurityParams as AcadSecurityParams
from .Objects.AcadSelectionSet import AcadSelectionSet as AcadSelectionSet
from .Objects.AcadSelectionSets import AcadSelectionSets as AcadSelectionSets
from .Objects.AcadSortentsTable import AcadSortentsTable as AcadSortentsTable
from .Objects.AcadState import AcadState as AcadState
from .Objects.AcadSubDMeshEdge import AcadSubDMeshEdge as AcadSubDMeshEdge
from .Objects.AcadSubDMeshFace import AcadSubDMeshFace as AcadSubDMeshFace
from .Objects.AcadSubDMeshVertex import AcadSubDMeshVertex as AcadSubDMeshVertex
from .Objects.AcadSubEntSolidEdge import AcadSubEntSolidEdge as AcadSubEntSolidEdge
from .Objects.AcadSubEntSolidFace import AcadSubEntSolidFace as AcadSubEntSolidFace
from .Objects.AcadSubEntSolidNode import AcadSubEntSolidNode as AcadSubEntSolidNode
from .Objects.AcadSubEntSolidVertex import AcadSubEntSolidVertex as AcadSubEntSolidVertex
from .Objects.AcadSubEntity import AcadSubEntity as AcadSubEntity
from .Objects.AcadSummaryInfo import AcadSummaryInfo as AcadSummaryInfo
from .Objects.AcadTableStyle import AcadTableStyle as AcadTableStyle
from .Objects.AcadTextStyle import AcadTextStyle as AcadTextStyle
from .Objects.AcadTextStyles import AcadTextStyles as AcadTextStyles
from .Objects.AcadToolbar import AcadToolbar as AcadToolbar
from .Objects.AcadToolbarItem import AcadToolbarItem as AcadToolbarItem
from .Objects.AcadToolbars import AcadToolbars as AcadToolbars
from .Objects.AcadUCS import AcadUCS as AcadUCS
from .Objects.AcadUCSs import AcadUCSs as AcadUCSs
from .Objects.AcadUtility import AcadUtility as AcadUtility
from .Objects.AcadView import AcadView as AcadView
from .Objects.AcadViewport import AcadViewport as AcadViewport
from .Objects.AcadViewports import AcadViewports as AcadViewports
from .Objects.AcadViews import AcadViews as AcadViews
from .Objects.AcadXRecord import AcadXRecord as AcadXRecord
from enum import IntEnum

class AccessMode(IntEnum):
    ReadWrite = 0
    ReadOnly = 1
    WriteOnly = 2
    DenyFromAll = 3

class proxy_property:
    rettype_name: str
    rettype: type
    propertyName: str
    mode: AccessMode
    def __init__(self, rettype: type, propertyName: str, mode: AccessMode) -> None: ...
    def __get__(self, instance, owner): ...
    def __set__(self, instance, value) -> None: ...
