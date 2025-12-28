from .Autocad.AcadEntity import *
from .Autocad.AcadObject import *
from .Autocad.Entities import *
from .Autocad.Objects import *
from .Types import *
from .Autocad.Proxy import *
from abc import ABC, abstractmethod


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



class BlockReference(ABC):
    def __init__(self, acad_block_reference:AcadBlockReference = None):
        self.acad_block_reference:AcadBlockReference = acad_block_reference
        self.Attributes = self._get_block_attributes(acad_block_reference)
        self.DynamicProperties = self._get_block_dynamic_properties(acad_block_reference)
    
    @staticmethod
    def _get_block_attributes(block_ref:AcadBlockReference):
        attrib = None
        if isinstance(block_ref, AcadBlockReference) and block_ref.HasAttributes:
            obj_arr = block_ref.GetAttributes()
            attrib:list[AcadAttributeReference] = []
            for attr in obj_arr:
                attrib.append(AcadAttributeReference(attr))
        return attrib

    @staticmethod
    def _get_block_dynamic_properties(block_ref:AcadBlockReference):
        dynprop = None
        if isinstance(block_ref, AcadBlockReference) and block_ref.IsDynamicBlock:
            dyn_arr = block_ref.GetDynamicBlockProperties()
            dynprop:list[AcadDynamicBlockReferenceProperty] = []
            for dattr in dyn_arr:
                dynprop.append(AcadDynamicBlockReferenceProperty(dattr))
        return dynprop

    @classmethod
    def read_from(cls, space: AcadModelSpace | AcadPaperSpace):
        for v in space:
            blk_ref = AcadBlockReference(v)
            if blk_ref.ObjectName == 'AcDbBlockReference' and blk_ref.EffectiveName == cls.BlockName:
                yield cls(blk_ref)

    @property
    @abstractmethod
    def BlockName(self) -> str: ...

    def insert(self, insertion_point:PyGePoint3d, space: AcadModelSpace | AcadPaperSpace | AcadBlock):
        block = space.InsertBlock(insertion_point, self.BlockName)
        if self.acad_block_reference:
            return type(self)(block)

        self.Attributes = self._get_block_attributes(block)
        self.DynamicProperties = self._get_block_dynamic_properties(block)
        self.acad_block_reference = block

    
    def attribute(self, tag_name: str) -> AcadAttributeReference:
        if self.acad_block_reference and self.Attributes:
            for attr in self.Attributes:
                if attr.TagString == tag_name:
                    return attr
    
    def dynamic_property(self, dyn_name: str) -> AcadDynamicBlockReferenceProperty:
        if self.acad_block_reference and self.DynamicProperties:
            for dyn in self.DynamicProperties:
                if dyn.PropertyName == dyn_name:
                    return dyn

    def get_attribute_value(self, tag_name) -> str:
        attr = self.attribute(tag_name)
        if attr: return attr.TextString

    def set_attribute_value(self, tag_name, value):
        attr = self.attribute(tag_name)
        if attr: attr.TextString = value
    
    def get_dynamic_property_value(self, dyn_name:str) -> Variant:
        dyn = self. dynamic_property(dyn_name)
        if dyn: return dyn.Value

    def set_dynamic_property_value(self, dyn_name, value):
        dyn = self. dynamic_property(dyn_name)
        if dyn: dyn.Value = value