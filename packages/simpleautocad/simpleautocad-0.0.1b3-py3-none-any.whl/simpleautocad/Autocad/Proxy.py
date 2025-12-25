from __future__ import annotations
from enum import IntEnum

class AccessMode(IntEnum):
    ReadWrite = 0
    ReadOnly = 1
    WriteOnly = 2
    DenyFromAll = 3

class proxy_property(): #Generic[T]
    def __init__(self, rettype: type, propertyName: str, mode: AccessMode):
        # Храним как строку ИЛИ как класс
        self.rettype_name = rettype if isinstance(rettype, str) else None
        self.rettype = rettype
        self.propertyName = propertyName
        self.mode = mode

    def __get__(self, instance, owner):
        if self.mode.value is AccessMode.WriteOnly.value:
            raise Exception(f"Свойство '{self.propertyName}' доступно только для записи.")
        if instance is None:
            return self
        # Если self.rettype_name - строка, динамически ищем класс
        target_type = None
        if self.rettype_name:
            try:
                # Ищем класс в глобальной области видимости или области видимости владельца (owner)
                target_type = globals().get(self.rettype_name) or getattr(owner, self.rettype_name, None)
                if not target_type:
                    raise NameError(f"Тип '{self.rettype_name}' не найден.")
                    # target_type = globals().get(self.rettype, None)
            except Exception as e: 
                # raise TypeError(f"Не удалось разрешить имя типа '{self.rettype_name}': {e}")
                pass
        else:
            target_type = self.rettype
        value = getattr(instance._obj, self.propertyName)
        if not target_type:
            return value
        else:
            return target_type(value)

    def __set__(self, instance, value):
        if self.mode is AccessMode.ReadOnly:
            raise AttributeError(f"Свойство '{self.propertyName}' доступно только для чтения.")
        # Логика установки значения в базовый объект
        try:
            if type(value).__mro__[-2] in (AppObject, Variant): value = value()
            setattr(instance._obj, self.propertyName, value)
        except AttributeError:
            raise AttributeError(f"Невозможно установить свойство '{self.propertyName}' в базовом объекте.")


from ..Types import *
from .Base import *

from .Objects.AcadAcCmColor import AcadAcCmColor
from .Objects.AcadApplication import AcadApplication
from .Objects.AcadBlock import AcadBlock
from .Objects.AcadBlocks import AcadBlocks
from .Objects.AcadDatabase import AcadDatabase, IAcadDatabase
from .Objects.AcadDatabasePreferences import AcadDatabasePreferences
from .Objects.AcadDictionaries import AcadDictionaries
from .Objects.AcadDictionary import AcadDictionary
from .Objects.AcadDimStyle import AcadDimStyle
from .Objects.AcadDimStyles import AcadDimStyles
from .Objects.AcadDocument import AcadDocument
from .Objects.AcadDocuments import AcadDocuments
from .Objects.AcadDynamicBlockReferenceProperty import AcadDynamicBlockReferenceProperty
from .Objects.AcadGroup import AcadGroup
from .Objects.AcadGroups import AcadGroups
from .Objects.AcadHyperlink import AcadHyperlink
from .Objects.AcadHyperlinks import AcadHyperlinks
from .Objects.AcadIDPair import AcadIDPair
from .Objects.AcadLayer import AcadLayer
from .Objects.AcadLayers import AcadLayers
from .Objects.AcadLayerStateManager import AcadLayerStateManager
from .Objects.AcadLayout import AcadLayout
from .Objects.AcadLayouts import AcadLayouts
from .Objects.AcadLineType import AcadLineType
from .Objects.AcadLineTypes import AcadLineTypes
from .Objects.AcadMaterial import AcadMaterial
from .Objects.AcadMaterials import AcadMaterials
from .Objects.AcadMenuBar import AcadMenuBar
from .Objects.AcadMenuGroup import AcadMenuGroup
from .Objects.AcadMenuGroups import AcadMenuGroups
from .Objects.AcadMLeaderLeader import AcadMLeaderLeader
from .Objects.AcadMLeaderStyle import AcadMLeaderStyle
from .Objects.AcadModelSpace import AcadModelSpace
from .Objects.AcadPaperSpace import AcadPaperSpace
from .Objects.AcadPlot import AcadPlot
from .Objects.AcadPlotConfiguration import AcadPlotConfiguration
from .Objects.AcadPlotConfigurations import AcadPlotConfigurations
from .Objects.AcadPopupMenu import AcadPopupMenu
from .Objects.AcadPopupMenuItem import AcadPopupMenuItem
from .Objects.AcadPopupMenus import AcadPopupMenus
from .Objects.AcadPreferences import AcadPreferences
from .Objects.AcadPreferencesDisplay import AcadPreferencesDisplay
from .Objects.AcadPreferencesDrafting import AcadPreferencesDrafting
from .Objects.AcadPreferencesFiles import AcadPreferencesFiles
from .Objects.AcadPreferencesOpenSave import AcadPreferencesOpenSave
from .Objects.AcadPreferencesOutput import AcadPreferencesOutput
from .Objects.AcadPreferencesProfiles import AcadPreferencesProfiles
from .Objects.AcadPreferencesSelection import AcadPreferencesSelection
from .Objects.AcadPreferencesSystem import AcadPreferencesSystem
from .Objects.AcadPreferencesUser import AcadPreferencesUser
from .Objects.AcadRegisteredApplication import AcadRegisteredApplication
from .Objects.AcadRegisteredApplications import AcadRegisteredApplications
from .Objects.AcadSectionManager import AcadSectionManager
from .Objects.AcadSectionSettings import AcadSectionSettings
from .Objects.AcadSectionTypeSettings import AcadSectionTypeSettings
from .Objects.AcadSecurityParams import AcadSecurityParams
from .Objects.AcadSelectionSet import AcadSelectionSet
from .Objects.AcadSelectionSets import AcadSelectionSets
from .Objects.AcadSortentsTable import AcadSortentsTable
from .Objects.AcadState import AcadState
from .Objects.AcadSubDMeshEdge import AcadSubDMeshEdge
from .Objects.AcadSubDMeshFace import AcadSubDMeshFace
from .Objects.AcadSubDMeshVertex import AcadSubDMeshVertex
from .Objects.AcadSubEntSolidEdge import AcadSubEntSolidEdge
from .Objects.AcadSubEntSolidFace import AcadSubEntSolidFace
from .Objects.AcadSubEntSolidNode import AcadSubEntSolidNode
from .Objects.AcadSubEntSolidVertex import AcadSubEntSolidVertex
from .Objects.AcadSummaryInfo import AcadSummaryInfo
from .Objects.AcadTableStyle import AcadTableStyle
from .Objects.AcadSubEntity import AcadSubEntity
from .Objects.AcadTextStyle import AcadTextStyle
from .Objects.AcadTextStyles import AcadTextStyles
from .Objects.AcadToolbar import AcadToolbar
from .Objects.AcadToolbarItem import AcadToolbarItem
from .Objects.AcadToolbars import AcadToolbars
from .Objects.AcadUCS import AcadUCS
from .Objects.AcadUCSs import AcadUCSs
from .Objects.AcadUtility import AcadUtility
from .Objects.AcadView import AcadView
from .Objects.AcadViewport import AcadViewport
from .Objects.AcadViewports import AcadViewports
from .Objects.AcadViews import AcadViews
from .Objects.AcadXRecord import AcadXRecord


from .Entities.Acad3DFace import Acad3DFace
from .Entities.Acad3DPolyline import Acad3DPolyline
from .Entities.Acad3DSolid import Acad3DSolid
from .Entities.AcadArc import AcadArc
from .Entities.AcadAttribute import AcadAttribute
from .Entities.AcadAttributeReference import AcadAttributeReference
from .Entities.AcadBlockReference import AcadBlockReference
from .Entities.AcadCircle import AcadCircle
from .Entities.AcadComparedReference import AcadComparedReference
from .Entities.AcadDgnUnderlay import AcadDgnUnderlay
from .Entities.AcadDim3PointAngular import AcadDim3PointAngular
from .Entities.AcadDimAligned import AcadDimAligned
from .Entities.AcadDimAngular import AcadDimAngular
from .Entities.AcadDimArcLength import AcadDimArcLength
from .Entities.AcadDimDiametric import AcadDimDiametric
from .Entities.AcadDimension import AcadDimension
from .Entities.AcadDimOrdinate import AcadDimOrdinate
from .Entities.AcadDimRadial import AcadDimRadial
from .Entities.AcadDimRadialLarge import AcadDimRadialLarge
from .Entities.AcadDimRotated import AcadDimRotated
from .Entities.AcadDwfUnderlay import AcadDwfUnderlay
from .Entities.AcadEllipse import AcadEllipse
from .Entities.AcadExternalReference import AcadExternalReference
from .Entities.AcadExtrudedSurface import AcadExtrudedSurface
from .Entities.AcadGeomapImage import AcadGeomapImage
from .Entities.AcadGeoPositionMarker import AcadGeoPositionMarker
from .Entities.AcadHatch import AcadHatch
from .Entities.AcadHelix import AcadHelix
from .Entities.AcadLeader import AcadLeader
from .Entities.AcadLine import AcadLine
from .Entities.AcadLoftedSurface import AcadLoftedSurface
from .Entities.AcadLWPolyline import AcadLWPolyline
from .Entities.AcadMInsertBlock import AcadMInsertBlock
from .Entities.AcadMLeader import AcadMLeader
from .Entities.AcadMLine import AcadMLine
from .Entities.AcadMtext import AcadMtext
from .Entities.AcadNurbSurface import AcadNurbSurface
from .Entities.AcadOle import AcadOle
from .Entities.AcadPdfUnderlay import AcadPdfUnderlay
from .Entities.AcadPlaneSurface import AcadPlaneSurface
from .Entities.AcadPoint import AcadPoint
from .Entities.AcadPointCloud import AcadPointCloud
from .Entities.AcadPointCloudEx import AcadPointCloudEx
from .Entities.AcadPolyfaceMesh import AcadPolyfaceMesh
from .Entities.AcadPolygonMesh import AcadPolygonMesh
from .Entities.AcadPolyline import AcadPolyline
from .Entities.AcadPViewport import AcadPViewport
from .Entities.AcadRasterImage import AcadRasterImage
from .Entities.AcadRay import AcadRay
from .Entities.AcadRegion import AcadRegion
from .Entities.AcadSection import AcadSection
from .Entities.AcadShape import AcadShape
from .Entities.AcadSolid import AcadSolid
from .Entities.AcadSpline import AcadSpline
from .Entities.AcadSubDMesh import AcadSubDMesh
from .Entities.AcadSurface import AcadSurface
from .Entities.AcadSweptSurface import AcadSweptSurface
from .Entities.AcadTable import AcadTable
from .Entities.AcadText import AcadText
from .Entities.AcadTolerance import AcadTolerance
from .Entities.AcadTrace import AcadTrace
from .Entities.AcadUnderlay import AcadUnderlay
from .Entities.AcadWipeout import AcadWipeout
from .Entities.AcadXline import AcadXline
