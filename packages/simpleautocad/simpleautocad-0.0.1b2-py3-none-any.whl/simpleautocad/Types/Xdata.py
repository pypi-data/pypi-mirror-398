from .VarType import *
from enum import IntEnum
from .Ac import AdeskDxfCode

class DxfGroupXDCode(IntEnum):
    """
    Перечисление кодов групп DXF, используемых для Extended Data (XData). [1000 - 1071]
    """
    # APP_NAME = AdeskDxfCode.kDxfRegAppName       # Строковое значение имени приложения (регистратора)
    # STRING = AdeskDxfCode.kDxfXdAsciiString         # Общее строковое значение XData
    # EXT_ASC_STRING = 1001 # Расширенная строка (для юникода)
    # CONTROL_STRING = 1002 # Строка управления (например, "{", "}")
    # LAYER_NAME = AdeskDxfCode.kDxfXdLayerName     # Имя слоя
    # DATABASE_HANDLE = 1005 # Дескриптор базы данных
    # POSITION_X = 1010     # X-координата позиции (3D точка, индексы 10, 20, 30 вместе)
    # POSITION_Y = 1020     # Y-координата позиции
    # POSITION_Z = 1030     # Z-координата позиции
    # DISTANCE = 1040       # Значение расстояния (с плавающей точкой)
    # SCALE = 1041          # Значение масштаба (с плавающей точкой)
    # INTEGER_16 = 1070     # 16-битное целое число (Short)
    # INTEGER_32 = 1071     # 32-битное целое число (Long/Int)
    kDxfXdAsciiString  = AdeskDxfCode.kDxfXdAsciiString
    kDxfRegAppName     = AdeskDxfCode.kDxfRegAppName
    kDxfXdControlString = AdeskDxfCode.kDxfXdControlString
    kDxfXdLayerName    = AdeskDxfCode.kDxfXdLayerName
    kDxfXdBinaryChunk  = AdeskDxfCode.kDxfXdBinaryChunk
    kDxfXdHandle       = AdeskDxfCode.kDxfXdHandle

    kDxfXdXCoord       = AdeskDxfCode.kDxfXdXCoord
    # kDxfXdYCoord       = AdeskDxfCode.kDxfXdYCoord
    # kDxfXdZCoord       = AdeskDxfCode.kDxfXdZCoord

    kDxfXdWorldXCoord  = AdeskDxfCode.kDxfXdWorldXCoord
    # kDxfXdWorldYCoord  = AdeskDxfCode.kDxfXdWorldYCoord
    # kDxfXdWorldZCoord  = AdeskDxfCode.kDxfXdWorldZCoord

    kDxfXdWorldXDisp   = AdeskDxfCode.kDxfXdWorldXDisp
    # kDxfXdWorldYDisp   = AdeskDxfCode.kDxfXdWorldYDisp
    # kDxfXdWorldZDisp   = AdeskDxfCode.kDxfXdWorldZDisp

    kDxfXdWorldXDir    = AdeskDxfCode.kDxfXdWorldXDir
    # kDxfXdWorldYDir    = AdeskDxfCode.kDxfXdWorldYDir
    # kDxfXdWorldZDir    = AdeskDxfCode.kDxfXdWorldZDir

    kDxfXdReal         = AdeskDxfCode.kDxfXdReal
    kDxfXdDist         = AdeskDxfCode.kDxfXdDist
    kDxfXdScale        = AdeskDxfCode.kDxfXdScale

    kDxfXdInteger16    = AdeskDxfCode.kDxfXdInteger16
    kDxfXdInteger32    = AdeskDxfCode.kDxfXdInteger32


class XDataManager():
    def __init__(self, regAppName: str = ''):
        self._codes = [DxfGroupXDCode.kDxfRegAppName]
        self._values = [regAppName]

    @property
    def RegAppName(self) -> str:
        return self._values[0]

    @RegAppName.setter
    def RegAppName(self, value: str) -> str:
        self._values[0] = value

    @property
    def xDataType(self) -> vShortArray:
        return vShortArray(self._codes)

    @property
    def xDataValue(self) -> vVariantArray:
        return vVariantArray(self._values)
    
    def add_data(self, group_code: DxfGroupXDCode|list[DxfGroupXDCode]|tuple[DxfGroupXDCode], value: int|str|float|list[int|str|float]|tuple[int|str|float]):
        self._codes += flatten_generic(group_code)
        self._values += flatten_generic(value)
        if len(self._codes) != len(self._values): raise IndexError(f'Каждому коду должно соответствовать значение. Кодов: {len(self._codes)}, значений: {len(self._values)}')

    def __getitem__(self, key):
        return self._codes[key], self._values[key]

    def __setitem__(self, key, value):
        if isinstance(value, (list, tuple)) and len(value)==2:
            self._codes[key] = DxfGroupXDCode(value[0])
            self._values[key] = value[1]
        else:
            raise ValueError(f'Не допустимое кол-во элементов или не верный тип данных: {value}')
            
    def __len__(self):
            return len(self._codes)

    def __iter__(self):
        for i in range(0,len(self._codes)):
            yield self._codes[i], self._values[i]

    def __repr__(self):
        return f'{self.__class__.__name__}({self.xDataType}, {self.xDataValue})'