from __future__ import annotations
from ..VarType import *
from .Matrix import *
from .Vector import *
import math

class PyGePoint3d(vDoubleArray):
    """3d координаты точки"""
    def __init__(self, *args):
        """x=0.0, y=0.0, z=0.0"""
        super().__init__(*args, check_count = 3, set_default = 0.0)

    @property
    def x(self): return self[0]
    @x.setter
    def x(self, value): self[0] = value
    @property
    def y(self): return self[1]
    @y.setter
    def y(self, value): self[1] = value
    @property
    def z(self): return self[2]
    @z.setter
    def z(self, value): self[2] = value

    def __add__(self, vector: PyGeVector3d) -> PyGePoint3d:
        """Сложение точки с вектором (Point + Vector)"""
        if isinstance(vector, PyGeVector3d):
            return PyGePoint3d(self.x + vector.x,self.y + vector.y, self.z + vector.z)
        raise TypeError(f"Неподдерживаемый тип операнда {type(vector)}")
    
    def __sub__(self, other: PyGePoint3d|PyGeVector3d) -> PyGeVector3d|PyGePoint3d:
        """
        Вычитание:
        1. Точка - Точка = Вектор (Point - Point = Vector)
        2. Точка - Вектор = Точка (Point - Vector = Point)
        """
        if isinstance(other, PyGePoint3d):
            return PyGeVector3d(self.x - other.x, self.y - other.y, self.x - other.z)
        elif isinstance(other, PyGeVector3d):
            return PyGePoint3d(self.x - other.x, self.y - other.y, self.z - other.z)
        raise TypeError(f"Неподдерживаемый тип операнда {type(other)}")

    def __mul__(self, scalar: int|float) -> PyGePoint3d:
        """Умножение точки на скаляр (Point * Scalar)"""
        if isinstance(scalar, (int,float)):
            return PyGePoint3d(self.x * scalar, self.y * scalar, self.z * scalar)
        raise TypeError(f"Неподдерживаемый тип операнда {type(scalar)}")

    def __rmul__(self, scalar: int|float) -> PyGePoint3d:
        """Зеркальное умножение на скаляр (Scalar * Point)"""
        return self.__mul__(scalar)

    def __truediv__(self, scalar: int|float) -> PyGePoint3d:
        """Деление точки на скаляр (Point / Scalar)"""
        if isinstance(scalar, (int,float)):
            if scalar == 0:
                raise ZeroDivisionError("Деление на ноль невозможно.")
            return PyGePoint3d(self.x / scalar, self.y / scalar, self.z / scalar)
        raise TypeError(f"Неподдерживаемый тип операнда {type(scalar)}")
    
    def __iadd__(self, vector: PyGeVector3d) -> PyGePoint3d:
        """Оператор += (Point += Vector)"""
        if isinstance(vector, PyGeVector3d):
            self.x += vector.x
            self.y += vector.y
            self.z += vector.z
            return self
        raise TypeError(f"Неподдерживаемый тип операнда {type(vector)}")

    def __isub__(self, vector: PyGeVector3d) -> PyGePoint3d:
        """Оператор -= (Point -= Vector)"""
        if isinstance(vector, PyGeVector3d):
            self.x -= vector.x
            self.y -= vector.y
            self.z -= vector.z
            return self
        raise TypeError(f"Неподдерживаемый тип операнда {type(vector)}")

    def __imul__(self, scalar: int|float) -> PyGePoint3d:
        """Оператор *= (Point *= Scalar)"""
        if isinstance(scalar, (int, float)):
            self.x *= scalar
            self.y *= scalar
            self.z *= scalar
            return self
        raise TypeError(f"Неподдерживаемый тип операнда {type(scalar)}")
        
    def __itruediv__(self, scalar: int|float) -> PyGePoint3d:
        """Оператор /= (Point /= Scalar)"""
        if isinstance(scalar, (int,float)):
            if scalar == 0:
                raise ZeroDivisionError("Деление на ноль невозможно.")
            self.x /= scalar
            self.y /= scalar
            self.z /= scalar
        raise TypeError(f"Неподдерживаемый тип операнда {type(scalar)}")

    def asVector(self) -> PyGeVector3d:
        """Преобразует точку в вектор, считая ее радиус-вектором от начала координат"""
        return PyGeVector3d(self)
    
    def distanceTo(self, other: PyGePoint3d) -> float:
        """Вычисляет расстояние до другой точки"""
        if isinstance(other, PyGePoint3d):
            dx = self.x - other.x
            dy = self.y - other.y
            dz = self.z - other.z
            return math.sqrt(dx**2 + dy**2 + dz**2)
        raise TypeError(f"Неподдерживаемый тип операнда {type(other)}")
    
    def isEqualTo(self, other_point: PyGePoint3d, tolerance = 1e-9) -> bool:
        """Проверяет равенство точек с учетом допуска"""
        return self.distanceTo(other_point) <= tolerance
    
    def transformBy(self, matrix: PyGeMatrix3d) -> None:
        """Трансформирует текущую точку с помощью матрицы трансформации 4x4."""
        if not isinstance(matrix, PyGeMatrix3d):
            raise TypeError(f"Неподдерживаемый тип операнда {type(matrix)}")
        # Точка в гомогенных координатах: [x, y, z, 1]
        point_vector = np.array([self.x, self.y, self.z, 1.0])
        # Выполняем матричное умножение: M * P
        transformed_point_vector = matrix.matrix @ point_vector
        # Обновляем координаты текущего объекта
        # 0, 1, 2 индексы содержат новые x, y, z
        self.x = transformed_point_vector[0]
        self.y = transformed_point_vector[1]
        self.z = transformed_point_vector[2]
        # return self

    def __str__(self):
        return f"{self.__class__.__name__}(x={self.x:.8f}, y={self.y:.8f}, z={self.z:.8f})"
        
        
        
class PyGePoint2d(vDoubleArray):
    """2d координаты точки"""
    def __init__(self, *args):
        """x=0.0, y=0.0"""
        super().__init__(*args, check_count = 2, set_default = 0.0)

    @property
    def x(self): return self[0]
    @x.setter
    def x(self, value): self[0] = value
    @property
    def y(self): return self[1]
    @y.setter
    def y(self, value): self[1] = value

    def __add__(self, vector: PyGeVector2d) -> PyGePoint2d:
        """Сложение точки с вектором (Point + Vector = Point)"""
        if isinstance(vector, PyGeVector3d):
            return PyGePoint2d(self.x + vector.x,self.y + vector.y)
        raise TypeError(f"Неподдерживаемый тип операнда {type(vector)}")
    
    def __sub__(self, other: PyGePoint2d|PyGeVector2d) -> PyGeVector2d|PyGePoint2d:
        """
        Вычитание:
        1. Точка - Точка = Вектор (Point - Point = Vector)
        2. Точка - Вектор = Точка (Point - Vector = Point)
        """
        if isinstance(other, PyGePoint2d):
            return PyGeVector2d(self.x - other.x, self.y - other.y)
        elif isinstance(other, PyGeVector2d):
            return PyGePoint2d(self.x - other.x, self.y - other.y)
        raise TypeError(f"Неподдерживаемый тип операнда {type(other)}")

    def __mul__(self, scalar: int|float) -> PyGePoint2d:
        """Умножение точки на скаляр (Point * Scalar)"""
        if isinstance(scalar, (int,float)):
            return PyGePoint2d(self.x * scalar, self.y * scalar)
        raise TypeError(f"Неподдерживаемый тип операнда {type(scalar)}")

    def __rmul__(self, scalar: int|float) -> PyGePoint2d:
        """Зеркальное умножение на скаляр (Scalar * Point)"""
        return self.__mul__(scalar)

    def __truediv__(self, scalar: int|float) -> PyGePoint2d:
        """Деление точки на скаляр (Point / Scalar)"""
        if isinstance(scalar, (int,float)):
            if scalar == 0:
                raise ZeroDivisionError("Деление на ноль невозможно.")
            return PyGePoint2d(self.x / scalar, self.y / scalar)
        raise TypeError(f"Неподдерживаемый тип операнда {type(scalar)}")
    
    def __iadd__(self, vector: PyGeVector2d) -> PyGePoint2d:
        """Оператор += (Point += Vector)"""
        if isinstance(vector, PyGeVector2d):
            self.x += vector.x
            self.y += vector.y
            return self
        raise TypeError(f"Неподдерживаемый тип операнда {type(vector)}")

    def __isub__(self, vector: PyGeVector2d) -> PyGePoint2d:
        """Оператор -= (Point -= Vector)"""
        if isinstance(vector, PyGeVector2d):
            self.x -= vector.x
            self.y -= vector.y
            return self
        raise TypeError(f"Неподдерживаемый тип операнда {type(vector)}")

    def __imul__(self, scalar: int|float) -> PyGePoint2d:
        """Оператор *= (Point *= Scalar)"""
        if isinstance(scalar, (int, float)):
            self.x *= scalar
            self.y *= scalar
            return self
        raise TypeError(f"Неподдерживаемый тип операнда {type(scalar)}")
        
    def __itruediv__(self, scalar: int|float) -> PyGePoint2d:
        """Оператор /= (Point /= Scalar)"""
        if isinstance(scalar, (int,float)):
            if scalar == 0:
                raise ZeroDivisionError("Деление на ноль невозможно.")
            self.x /= scalar
            self.y /= scalar
        raise TypeError(f"Неподдерживаемый тип операнда {type(scalar)}")

    def asVector(self) -> PyGeVector2d:
        """Преобразует точку в вектор, считая ее радиус-вектором от начала координат"""
        return PyGeVector2d(self)
    
    def distanceTo(self, other: PyGePoint2d) -> float:
        """Вычисляет расстояние до другой точки"""
        if isinstance(other, PyGeVector2d):
            dx = self.x - other.x
            dy = self.y - other.y
            return math.sqrt(dx**2 + dy**2)
        raise TypeError(f"Неподдерживаемый тип операнда {type(other)}")
    
    def isEqualTo(self, other: PyGePoint2d, tolerance = 1e-9) -> bool:
        """Проверяет равенство точек с учетом допуска"""
        return self.distanceTo(other) <= tolerance
    
    def transformBy(self, matrix: PyGeMatrix2d) -> PyGePoint2d:
        """Трансформирует текущую точку с помощью матрицы трансформации 4x4."""
        if not isinstance(matrix, PyGeMatrix2d):
            raise TypeError("Аргумент должен быть объектом PyGeMatrix3d.")
        # Точка в гомогенных координатах: [x, y, 1]
        point_vector = np.array([self.x, self.y, 1.0])
        # Выполняем матричное умножение: M * P
        # NumPy @ operator выполняет матричное умножение
        transformed_point_vector = matrix.matrix @ point_vector
        # Обновляем координаты текущего объекта
        # 0, 1 индексы содержат новые x, y
        self.x = transformed_point_vector[0]
        self.y = transformed_point_vector[1]
        return self

    def __str__(self):
        return f"{self.__class__.__name__}(x={self.x:.8f}, y={self.y:.8f})"



class PyGePoint3dArray(vDoubleArray):
    def __init__(self, *args):
        arglist = flatten_generic(list(args))
        points3d: list[PyGePoint3d] = []
        for i in range(0, len(arglist), 3):
            chunk = arglist[i:i + 3]
            points3d.append(PyGePoint3d(chunk))
        super().__init__(points3d)

    def __iter__(self):
        for i in range(0, len(self._value_py), 3):
            yield self._value_py[i:i+3]

    def __getitem__(self, index):
        start_index = index * 3
        end_index = start_index + 3
        if end_index > len(self._value_py) and start_index < len(self._value_py):
             return PyGePoint3d(self._value_py[start_index:])
        elif end_index <= len(self._value_py):
            return PyGePoint3d(self._value_py[start_index:end_index])
        else:
            raise IndexError("Out of range")

    def __setitem__(self, index, value):
        if (not isinstance(value, (PyGePoint3d, PyGePoint3dArray))) or (len(value) % 3):
            raise ValueError("Значение должно быть 3-х координатной точкой или массивом точек")
        start_index = index * 3
        end_index = start_index + len(value)
        if end_index <= len(self._value_py):
            self._value_py[start_index:end_index] = value
        else:
            raise IndexError("Вне диапазона")
            
    def __len__(self):
        return int(len(self._value_py) / 3)

    def __add__(self, other):
        if isinstance(other, (PyGePoint3d, PyGePoint3dArray)):
            data_float = self._value_py + other._value_py
        elif isinstance(other, (list,tuple,vDoubleArray)):
            if len(other) % 3:
                raise IndexError("Вне диапазона")
            data_float = self._value_py + flatten_generic(other)
        else:
            raise TypeError(f"Неподдерживаемый тип операнда для сложения: '{other.__class__.__name__}'")
        return PyGePoint3dArray(data_float)
    
    def __repr__(self):
        return f"{self.__class__.__name__}{[PyGePoint3d(v) for v in self]}"
    # def __str__(self):
    #     return f"{tuple([PyGePoint3d(v) for v in self])}"



class PyGePoint2dArray(vDoubleArray):
    def __init__(self, *args):
        arglist = flatten_generic(list(args))
        points2d: list[PyGePoint2d] = []
        for i in range(0, len(arglist), 2):
            chunk = arglist[i:i + 2]
            points2d.append(PyGePoint2d(chunk))
        super().__init__(points2d)

    def __iter__(self):
        for i in range(0, len(self._value_py), 2):
            yield self._value_py[i:i+2]

    def __getitem__(self, index):
        start_index = index * 2
        end_index = start_index + 2
        if end_index > len(self._value_py) and start_index < len(self._value_py):
             return PyGePoint2d(self._value_py[start_index:])
        elif end_index <= len(self._value_py):
            return PyGePoint2d(self._value_py[start_index:end_index])
        else:
            raise IndexError("Вне диапазона")

    def __setitem__(self, index, value):
        if (not isinstance(value, (PyGePoint2d, PyGePoint2dArray))) or (len(value) % 2):
            raise ValueError("Значение должно быть 2-х координатной точкой или массивом точек")
        start_index = index * 2
        end_index = start_index + len(value)
        if end_index <= len(self._value_py):
            self._value_py[start_index:end_index] = value
        else:
            raise IndexError("Вне диапазона")
            
    def __len__(self):
        return int(len(self._value_py) / 2)

    def __add__(self, other):
        if isinstance(other, (PyGePoint2d, PyGePoint2dArray)):
            data_float = self._value_py + other._value_py
        elif isinstance(other, (list,tuple,vDoubleArray)):
            if len(other) % 2:
                raise IndexError("Вне диапазона")
            data_float = self._value_py + flatten_generic(other)
        else:
            raise TypeError(f"Неподдерживаемый тип операнда для сложения: '{other.__class__.__name__}'")
        return PyGePoint2dArray(data_float)
    
    def __repr__(self):
        return f"{self.__class__.__name__}{[PyGePoint2d(v) for v in self]}"
