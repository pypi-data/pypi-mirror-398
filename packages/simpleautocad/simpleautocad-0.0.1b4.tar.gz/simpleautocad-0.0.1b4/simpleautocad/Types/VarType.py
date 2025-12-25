from win32com.client import VARIANT
import pythoncom
import array
import numpy as np
from enum import IntEnum
from collections.abc import Iterable



def is_iterable(obj):
    return isinstance(obj, Iterable) and not isinstance(obj, (str, bytes, bytearray))

def flatten_generic(nested_iterable):
    flat_list = []
    if is_iterable(nested_iterable):
        for item in nested_iterable:
            if is_iterable(item):
                flat_list.extend(flatten_generic(item))
            else:
                flat_list.append(item)
    else:
        flat_list.append(nested_iterable)
    return flat_list

class VT(IntEnum):
    BOOL            = pythoncom.VT_BOOL
    FLOAT           = pythoncom.VT_R4
    DOUBLE          = pythoncom.VT_R8
    LONG            = pythoncom.VT_I8
    INT             = pythoncom.VT_I4
    SHORT           = pythoncom.VT_I2
    STRING          = pythoncom.VT_BSTR
    OBJECT          = pythoncom.VT_DISPATCH
    VARIANT         = pythoncom.VT_VARIANT
    EMPTY           = pythoncom.VT_EMPTY
    NULL            = pythoncom.VT_NULL
    ARRAY           = pythoncom.VT_ARRAY
    ARRAY_BOOL      = BOOL | ARRAY
    ARRAY_FLOAT     = FLOAT | ARRAY
    ARRAY_DOUBLE    = DOUBLE | ARRAY
    ARRAY_LONG      = LONG | ARRAY
    ARRAY_INT       = INT | ARRAY
    ARRAY_SHORT     = SHORT | ARRAY
    ARRAY_STRING    = STRING | ARRAY
    ARRAY_OBJECT    = OBJECT | ARRAY
    ARRAY_VARIANT   = VARIANT | ARRAY

class Variant():

    VT_TYPE_MAP = {
        int: VT.LONG, 
        float: VT.DOUBLE, 
        str: VT.STRING, 
        bool: VT.BOOL, 
        type(None): VT.EMPTY
    }

    def __init__(self, value, force_vt_type:VT = None):
        self._vt_type_initial:VT = None
        self._value_py:any = None
        self._force_iterable:bool = False
        if isinstance(value, Variant):
            self._value_py = value._value_py
            self._vt_type_initial = value._vt_type_initial
            return
        if isinstance(value, (array.array, np.ndarray)):
            if force_vt_type is None:
                raise ValueError("Необходимо указать тип значений массива")
            self._value_py = value
            self._vt_type_initial = force_vt_type
            return
        self._process_value(value, force_vt_type)

    @property
    def value(self):
        if self._vt_type_initial in (VT.NULL, VT.EMPTY):
            return None
        if self._force_iterable and not is_iterable(self._value_py):
            return [self._value_py]
        else:
            return self._value_py
    @property
    def variant(self): 
        return self.to_variant()

    @property
    def varianttype(self) -> VT:
        return VT(self._vt_type_initial)

    @property
    def valuetype(self) -> type:
        if self._force_iterable:
            t = type(self[0])
        else:
            self._force_iterable = True
            t = type(self[0])
            self._force_iterable = False
        return t

    @staticmethod
    def _convert_to_type(value, target_vt_type):
        if target_vt_type in (VT.SHORT, VT.INT, VT.LONG):
            try:
                return int(value)
            except (ValueError, TypeError):
                raise TypeError(f"Невозможно преобразовать '{value}' в целое число для типа VT_I.")
        elif target_vt_type in (VT.FLOAT, VT.DOUBLE):
            try:
                return float(value)
            except (ValueError, TypeError):
                raise TypeError(f"Невозможно преобразовать '{value}' в float для типа VT_R.")
        elif target_vt_type == VT.STRING:
            return str(value)
        elif target_vt_type == VT.BOOL:
            return bool(value)
        return value

    @staticmethod
    def _unpack_variant_recursive(value):
        if isinstance(value, VARIANT):
            unpacked_value = value.value
            return Variant._unpack_variant_recursive(unpacked_value)
        elif isinstance(value, (list, tuple)):
            return [Variant._unpack_variant_recursive(item) for item in value]
        else:
            return value

    def _process_value(self, value, force_vt_type=None):
        """Централизованная функция обработки значения, используется в __init__ и set_value."""
        if force_vt_type is not None:
            # Логика принудительного типа
            self._vt_type_initial = force_vt_type
            if force_vt_type & VT.ARRAY:
                data_list = value if isinstance(value, (list, tuple)) else [value]
                base_type_vt = force_vt_type ^ VT.ARRAY
                self._value_py = [self._convert_to_type(item, base_type_vt) for item in data_list]
            else:
                self._value_py = self._convert_to_type(value, force_vt_type)
        else:
            # Логика автоматического определения типа (если не было принудительного указания в __init__)
            # Если тип уже был установлен автоматически при инициализации, используем его для приведения
            if self._vt_type_initial is not None and not (self._vt_type_initial & VT.ARRAY):
                 self._value_py = self._convert_to_type(value, self._vt_type_initial)
            else:
                 # Иначе определяем тип заново (например, для массивов или первой инициализации)
                 self._value_py = value
                 self._vt_type_initial = self._determine_vt_type(value)

    def _determine_vt_type(self, value):
        """Определяет базовый тип VT_* и флаги VT_ARRAY на основе первого элемента массива."""
        if isinstance(value, VARIANT):
            self._value_py = self._unpack_variant_recursive(value)
            return value.varianttype

        value_type = type(value)

        # 1. Если это базовый тип Python
        if value_type in self.VT_TYPE_MAP:
            return self.VT_TYPE_MAP[value_type]

        # 2. Если это итерируемый объект (список, кортеж)
        if isinstance(value, (list, tuple)):
            self._value_py = self._unpack_variant_recursive(value) # Убедимся, что данные чистые
            
            if not value:
                # Для пустого списка используем VT_VARIANT по умолчанию
                base_vt = VT.VARIANT
            else:
                # Определяем тип по первому элементу
                # Рекурсивно вызываем _determine_vt_type для первого элемента 
                base_vt = self._determine_vt_type(value[0])
                
                # Убедимся, что базовый тип не является сам массивом (мы хотим только базовый тип здесь)
                if base_vt & VT.ARRAY:
                    # Если первый элемент массива сам является массивом, оставляем VT_VARIANT
                    base_vt = VT.VARIANT
                # (В идеале здесь должна быть проверка, что все элементы списка имеют тот же базовый тип)
            return VT.ARRAY | base_vt

        # 3. Если тип не поддерживается
        raise ValueError(f"Неподдерживаемый тип данных: {value_type}")

    def set_iterable(self, is_iterable:bool = True):
        self._force_iterable = is_iterable

    def __iter__(self):
            """Делает объект итерируемым, если внутреннее значение является списком/кортежем."""
            if isinstance(self._value_py, (list, tuple)):
                return iter(self._value_py)
            else:
                # Если это не массив, вызываем TypeError (как обычные неитерируемые объекты Python)
                if self._force_iterable:
                    return iter([self._value_py])
                else:
                    raise TypeError(f"Объект {self.__class__.__name__} с типом {type(self._value_py)} не итерируем.")

    def __getitem__(self, key):
        """Получение элемента или среза по индексу (obj[0] или obj[1:3])."""
        if isinstance(self._value_py, (list, tuple)):
            return self._value_py[key]
        else:
            if self._force_iterable:
                return [self._value_py][key]
            else:
                raise TypeError(f"Объект {self.__class__.__name__} с типом {type(self._value_py)} не поддерживает индексацию.")

    def __setitem__(self, key, value):
        """Установка элемента или среза по индексу (obj[0] = value)."""
        if isinstance(self._value_py, list): # Работаем только с изменяемыми списками
            # Определяем базовый VT_тип для приведения нового значения
            if not (self._vt_type_initial & VT.ARRAY):
                 raise TypeError("Невозможно установить элемент по индексу для не-массива.")
            base_vt = self._vt_type_initial ^ VT.ARRAY
            # Если пользователь передал срез (slice), value будет списком
            if isinstance(key, slice):
                # Приводим каждый элемент нового списка к целевому типу
                converted_values = [self._convert_to_type(item, base_vt) for item in value]
                self._value_py[key] = converted_values
            else:
                # Если передан один индекс, приводим одно значение
                converted_value = self._convert_to_type(value, base_vt)
                self._value_py[key] = converted_value
        else:
            raise TypeError(f"Объект {self.__class__.__name__} с типом {type(self._value_py)} не поддерживает присваивание по индексу.")
            
    def __len__(self):
        """Возвращает длину объекта, если он является массивом."""
        if isinstance(self._value_py, (list, tuple)):
            return len(self._value_py)
        else:
            if self._force_iterable: return 1
            return 0 # Или вызвать TypeError, в зависимости от желаемого поведения

    def to_variant(self, force_vt_type:VT = None):
        target_vt = force_vt_type if force_vt_type is not None else self._vt_type_initial
        return VARIANT(target_vt, self._value_py)

    def __call__(self, force_vt_type=None): return self.to_variant(force_vt_type)

    def __str__(self):
        return f"{self.__class__.__name__}({self.varianttype!r}, {self.value})"

    def __repr__(self):
        return self.variant


vObjectEmpty = Variant(pythoncom.Empty, VT.OBJECT | VT.EMPTY)


class vObject(Variant):
    def __init__(self, obj):
        super().__init__(obj, force_vt_type=VT.OBJECT)

class vDouble(Variant):
    def __init__(self, double):
        super().__init__(double, force_vt_type=VT.DOUBLE)

class vLong(Variant):
    def __init__(self, long):
        super().__init__(long, force_vt_type=VT.LONG)

class vInteger(Variant):
    def __init__(self, integer):
        super().__init__(integer, force_vt_type=VT.INT)

class vShort(Variant):
    def __init__(self, boolean):
        super().__init__(boolean, force_vt_type=VT.SHORT)

class vBool(Variant):
    def __init__(self, boolean):
        super().__init__(boolean, force_vt_type=VT.BOOL)

class vString(Variant):
    def __init__(self, string):
        super().__init__(string, force_vt_type=VT.STRING)


class vArray(Variant):
    def __init__(self, *args, data_type:VT, check_count, set_default):
        arglist = flatten_generic(list(args))
        if check_count is not None:
            if set_default is not None:
                while len(arglist) < check_count:
                    arglist.append(set_default)
            if len(arglist) != check_count: 
                raise ValueError(f'Некорректное количество параметров: {len(arglist)}, ограничение: {check_count}')
        super().__init__(arglist, force_vt_type = VT.ARRAY | data_type)

class vObjectArray(vArray):
    def __init__(self, *args, check_count = None, set_default = None):
        super().__init__(args, data_type = VT.OBJECT, check_count = check_count, set_default = set_default)

class vVariantArray(vArray):
    def __init__(self, *args, check_count = None, set_default = None):
        super().__init__(*args, data_type = VT.VARIANT, check_count = check_count, set_default = set_default)

class vDoubleArray(vArray):
    def __init__(self, *args, check_count = None, set_default = None):
        super().__init__(*args, data_type = VT.DOUBLE, check_count = check_count, set_default = set_default)

class vLongArray(vArray):
    def __init__(self, *args, check_count = None, set_default = None):
        super().__init__(*args, data_type = VT.LONG, check_count = check_count, set_default = set_default)

class vStringArray(vArray):
    def __init__(self, *args, check_count = None, set_default = None):
        super().__init__(*args, data_type = VT.STRING, check_count = check_count, set_default = set_default)

class vIntegerArray(vArray):
    def __init__(self, *args, check_count = None, set_default = None):
        super().__init__(*args, data_type = VT.INT, check_count = check_count, set_default = set_default)

class vBoolArray(vArray):
    def __init__(self, *args, check_count = None, set_default = None):
        super().__init__(*args, data_type = VT.BOOL, check_count = check_count, set_default = set_default)

class vShortArray(vArray):
    def __init__(self, *args, check_count = None, set_default = None):
        super().__init__(*args, data_type = VT.SHORT, check_count = check_count, set_default = set_default)
