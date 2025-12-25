from .Autocad.AcadEntity import *
from .Autocad.AcadObject import *
from .Autocad.Entities import *
from .Autocad.Objects import *
from .Types import *
from .Autocad.Proxy import *


class AutoCAD(AcadApplication):
    _ACAD_TYPE_MAP = {
        'AcDbFace':Acad3DFace, # 3D-грань
        'AcDbPolygonMesh':AcadPolygonMesh, # Полигональная сеть
        'AcDb3dPolyline':Acad3DPolyline, # 3D-полилиния
        'AcDbArc':AcadArc, #Дуга
        'AcDbAttributeDefinition':AcadAttribute, # Определение атрибута
        'AcDb3dSolid':Acad3DSolid, # 3D-тело
        'AcDbCircle':AcadCircle, # Круг
        'AcDb3PointAngularDimension':AcadDim3PointAngular, # Угловой размер (3 точки)
        'AcDbAlignedDimension':AcadDimAligned, # Параллельный размер
        'AcDbDiametricDimension':AcadDimDiametric, # Диаметр
        'AcDbOrdinateDimension':AcadDimOrdinate, # Ординатный размер
        'AcDbRadialDimension':AcadDimRadial, # Размер радиуса
        'AcDbRotatedDimension':AcadDimRotated, # Повернутый размер
        'AcDbEllipse':AcadEllipse, # Эллипс
        'AcDbHatch':AcadHatch, # Штриховка
        'AcDbLeader':AcadLeader, # Выноска
        'AcDbMText':AcadMtext, # МТекст
        'AcDbText':AcadText, # Текст
        'AcDbPolyline':AcadLWPolyline, # Полилиния
        'AcDbLine':AcadLine, # Отрезок
        'AcDbMInsertBlock':AcadMInsertBlock, # Мн-блок
        'AcDbMLeader':AcadMLeader, # Мультивыноска
        'AcDbMline':AcadMLine, # МЛиния
        'AcDbPoint':AcadPoint, # Точка
        'AcDbPolyFaceMesh':AcadPolyfaceMesh, # Многогранная сеть
        'AcDb2dPolyline':AcadPolyline, # 2D-полилиния
        'AcDbRasterImage':AcadRasterImage, # Растровое изображение
        'AcDbRay':AcadRay, # Луч
        'AcDbRegion':AcadRegion, # Область
        'AcDbSection':AcadSection, # Объект сечения
        'AcDbShape':AcadShape, # Форма
        'AcDbSolid':AcadSolid, # Тело
        'AcDbSpline':AcadSpline, # Сплайн
        'AcDbTable':AcadTable, # Таблица
        'AcDbFcf':AcadTolerance, # Допуск
        'AcDbTrace':AcadTrace, # Полоса
        'AcDbXline':AcadXline, # Прямая
        'AcDbWipeout':AcadWipeout,
        'AcDbXrecord':AcadXRecord
        # 'AcDbBlockReference':(AcadExternalReference, AcadBlockReference), ##
    }

    def __init__(self):
        super().__init__(dispatch_object = None)

    def uGetAcadAcCmColor(self) -> AcadAcCmColor:
        progID = AcadApplication.__app_full_name__.replace('Application','AcCmColor')
        obj = self.GetInterfaceObject(progID)
        return AcadAcCmColor(obj)

    def uGetAcadLayerStateManager(self) -> AcadLayerStateManager:
        progID = AcadApplication.__app_full_name__.replace('Application','AcadLayerStateManager')
        obj = self.GetInterfaceObject(progID)
        return AcadLayerStateManager(obj)

    def uGetAcadSecurityParams(self) -> AcadSecurityParams:
        progID = AcadApplication.__app_full_name__.replace('Application','SecurityParams')
        obj = self.GetInterfaceObject(progID)
        return AcadSecurityParams(obj)

    def uSetXData(obj: AcadObject, xdm: XDataManager) -> None: 
        try:
            obj.Document.RegisteredApplications.Item(xdm.RegAppName)
        except:
            obj.Document.RegisteredApplications.Add(xdm.RegAppName)
        obj.SetXData(xdm.xDataType, xdm.xDataValue)

    def uGetObjectType(self, obj: AcadObject) -> type:
        return self._ACAD_TYPE_MAP.get(obj.ObjectName,None)