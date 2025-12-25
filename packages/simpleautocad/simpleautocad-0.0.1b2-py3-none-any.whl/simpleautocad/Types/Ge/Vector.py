from __future__ import annotations
from ..VarType import *
import math

class PyGeVector3d(vDoubleArray):
    def __init__(self, *args):
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

    def __add__(self, vector: PyGeVector3d) -> PyGeVector3d:
        """Сложение двух векторов (Vector + Vector)"""
        if isinstance(vector, PyGeVector3d):
            return PyGeVector3d(self.x + vector.x,self.y + vector.y, self.z + vector.z)
        raise TypeError(f"Неподдерживаемый тип операнда {type(vector)}")


    def __sub__(self, vector: PyGeVector3d) -> PyGeVector3d:
        """Вычитание двух векторов (Vector - Vector)"""
        if isinstance(vector, PyGeVector3d):
            return PyGeVector3d(self.x - vector.x, self.y - vector.y, self.z - vector.z)
        raise TypeError(f"Неподдерживаемый тип операнда {type(vector)}")

    def __mul__(self, scalar: int|float) -> PyGeVector3d:
        """Умножение вектора на скаляр (Vector * Scalar)"""
        if isinstance(scalar, (int, float)):
            return PyGeVector3d(self.x * scalar, self.y * scalar, self.z * scalar)
        raise TypeError(f"Неподдерживаемый тип операнда {type(scalar)}")

    def __rmul__(self, scalar: int|float) -> PyGeVector3d:
        """Зеркальное умножение на скаляр (Scalar * Vector)"""
        return self.__mul__(scalar)

    def __truediv__(self, scalar: int|float) -> PyGeVector3d:
        """Деление вектора на скаляр (Vector / Scalar)"""
        if isinstance(scalar, (int, float)):
            if scalar == 0:
                raise ZeroDivisionError("Деление на ноль невозможно.")
            return PyGeVector3d(self.x / scalar, self.y / scalar, self.z / scalar)
        raise TypeError(f"Неподдерживаемый тип операнда {type(scalar)}")
        
    def __neg__(self) -> PyGeVector3d:
        """Унарный минус (-Vector)"""
        return PyGeVector3d(-self.x, -self.y, -self.z)

    def __iadd__(self, vector) -> PyGeVector3d:
        """Оператор += (Vector += Vector)"""
        if isinstance(vector, PyGeVector3d):
            self.x += vector.x
            self.y += vector.y
            self.z += vector.z
            return self
        raise TypeError(f"Неподдерживаемый тип операнда {type(vector)}")

    def __isub__(self, vector) -> PyGeVector3d:
        """Оператор -= (Vector -= Vector)"""
        if isinstance(vector, PyGeVector3d):
            self.x -= vector.x
            self.y -= vector.y
            self.z -= vector.z
            return self
        raise TypeError(f"Неподдерживаемый тип операнда {type(vector)}")
            
    def __imul__(self, scalar) -> PyGeVector3d:
        """Оператор *= (Vector *= Scalar)"""
        if isinstance(scalar, (int, float)):
            self.x *= scalar
            self.y *= scalar
            self.z *= scalar
            return self
        raise TypeError(f"Неподдерживаемый тип операнда {type(scalar)}")
        
    def __itruediv__(self, scalar) -> PyGeVector3d:
        """Оператор /= (Vector /= Scalar)"""
        if isinstance(scalar, (int, float)):
            if scalar == 0:
                raise ZeroDivisionError("Деление на ноль невозможно.")
            self.x /= scalar
            self.y /= scalar
            self.z /= scalar
            return self
        raise TypeError(f"Неподдерживаемый тип операнда {type(scalar)}")

    def length(self) -> float:
        """Возвращает длину (магнитуду) вектора"""
        return math.sqrt(self.lengthSqrd())
    
    def lengthSqrd(self) -> float:
        """Возвращает квадрат длины вектора"""
        # Можно использовать вместо length() для сравнения длин 2 векторов (быстрее length())
        return self.x**2 + self.y**2 + self.z**2

    def normalize(self) -> None:
        """Нормализует вектор (делает его единичным)"""
        len_val = self.length()
        if len_val == 0:
            raise ZeroDivisionError("Невозможно нормализовать нулевой вектор.")
        self.x /= len_val
        self.y /= len_val
        self.z /= len_val
        # return self

    def normal(self) -> PyGeVector3d:
        """Возвращает новый нормализованный (единичный) вектор"""
        len_val = self.length()
        if len_val == 0:
            raise ZeroDivisionError("Невозможно получить нормаль от нулевого вектора.")
        return PyGeVector3d(self.x / len_val, self.y / len_val, self.z / len_val)
        
    def dotProduct(self, vector: PyGeVector3d) -> float:
        """Скалярное произведение векторов"""
        if isinstance(vector, PyGeVector3d):
            return (self.x * vector.x + 
                    self.y * vector.y + 
                    self.z * vector.z)
        raise TypeError(f"Неподдерживаемый тип операнда {type(vector)}")

    def crossProduct(self, vector: PyGeVector3d) -> PyGeVector3d:
        """Векторное произведение векторов"""
        if isinstance(vector, PyGeVector3d):
            i = self.y * vector.z - self.z * vector.y
            j = self.z * vector.x - self.x * vector.z
            k = self.x * vector.y - self.y * vector.x
            return PyGeVector3d(i, j, k)
        raise TypeError(f"Неподдерживаемый тип операнда {type(vector)}")
        
    def angleTo(self, vector: PyGeVector3d) -> float:
        """Вычисляет угол между двумя векторами в радианах"""
        if isinstance(vector, PyGeVector3d):
            # cos(theta) = (A . B) / (|A| * |B|)
            dot = self.dotProduct(vector)
            len1 = self.length()
            len2 = vector.length()
            if len1 == 0 or len2 == 0:
                return 0.0 # Угол для нулевых векторов не определен
            # Ограничиваем значение в диапазоне [-1, 1] для безопасности acos при ошибках округления
            cosine_angle = max(-1.0, min(dot / (len1 * len2), 1.0))
            return math.acos(cosine_angle)
        raise TypeError(f"Неподдерживаемый тип операнда {type(vector)}")

    def isEqualTo(self, vector: PyGeVector3d, tolerance = 1e-9) -> bool:
        """Проверяет равенство векторов с учетом допуска"""
        if isinstance(vector, PyGeVector3d):
            dx = abs(self.x - vector.x)
            dy = abs(self.y - vector.y)
            dz = abs(self.z - vector.z)
            return dx <= tolerance and dy <= tolerance and dz <= tolerance
        raise TypeError(f"Неподдерживаемый тип операнда {type(vector)}")

    def negate(self) -> None:
        """Инвертирует вектор"""
        self.x = -self.x
        self.y = -self.y
        self.z = -self.z
        # return self
    

    # def __repr__(self):
    #     return f"{self.__class__.__name__}(x={self.x}, y={self.y}, z={self.z})"
    def __str__(self):
        return f"{self.__class__.__name__}(x={self.x}, y={self.y}, z={self.z})"
    
    kIdentity:PyGeVector3d
    kXaxis:PyGeVector3d
    kYaxis:PyGeVector3d
    kZaxis:PyGeVector3d

PyGeVector3d.kIdentity  = PyGeVector3d(0.0, 0.0, 0.0) # Нулевой вектор
PyGeVector3d.kXaxis     = PyGeVector3d(1.0, 0.0, 0.0) # Единичный вектор X
PyGeVector3d.kYaxis     = PyGeVector3d(0.0, 1.0, 0.0) # Единичный вектор Y
PyGeVector3d.kZaxis     = PyGeVector3d(0.0, 0.0, 1.0) # Единичный вектор Z







class PyGeVector2d(vDoubleArray):
    def __init__(self, *args):
        super().__init__(*args, check_count = 2, set_default = 0.0)

    @property
    def x(self): return self[0]
    @x.setter
    def x(self, value): self[0] = value
    @property
    def y(self): return self[1]
    @y.setter
    def y(self, value): self[1] = value

    def __add__(self, vector: PyGeVector2d) -> PyGeVector3d:
        """Сложение двух векторов (Vector + Vector)"""
        if isinstance(vector, PyGeVector2d):
            return PyGeVector2d(self.x + vector.x,self.y + vector.y)
        raise TypeError(f"Неподдерживаемый тип операнда {type(vector)}")


    def __sub__(self, vector: PyGeVector2d) -> PyGeVector2d:
        """Вычитание двух векторов (Vector - Vector)"""
        if isinstance(vector, PyGeVector2d):
            return PyGeVector2d(self.x - vector.x, self.y - vector.y)
        raise TypeError(f"Неподдерживаемый тип операнда {type(vector)}")

    def __mul__(self, scalar: int|float) -> PyGeVector2d:
        """Умножение вектора на скаляр (Vector * Scalar)"""
        if isinstance(scalar, (int, float)):
            return PyGeVector2d(self.x * scalar, self.y * scalar)
        raise TypeError(f"Неподдерживаемый тип операнда {type(scalar)}")

    def __rmul__(self, scalar: int|float) -> PyGeVector2d:
        """Зеркальное умножение на скаляр (Scalar * Vector)"""
        return self.__mul__(scalar)

    def __truediv__(self, scalar: int|float) -> PyGeVector2d:
        """Деление вектора на скаляр (Vector / Scalar)"""
        if isinstance(scalar, (int, float)):
            if scalar == 0:
                raise ZeroDivisionError("Деление на ноль невозможно.")
            return PyGeVector2d(self.x / scalar, self.y / scalar)
        raise TypeError(f"Неподдерживаемый тип операнда {type(scalar)}")
        
    def __neg__(self) -> PyGeVector2d:
        """Унарный минус (-Vector)"""
        return PyGeVector2d(-self.x, -self.y)

    def __iadd__(self, vector) -> PyGeVector2d:
        """Оператор += (Vector += Vector)"""
        if isinstance(vector, PyGeVector2d):
            self.x += vector.x
            self.y += vector.y
            return self
        raise TypeError(f"Неподдерживаемый тип операнда {type(vector)}")

    def __isub__(self, vector) -> PyGeVector2d:
        """Оператор -= (Vector -= Vector)"""
        if isinstance(vector, PyGeVector2d):
            self.x -= vector.x
            self.y -= vector.y
            return self
        raise TypeError(f"Неподдерживаемый тип операнда {type(vector)}")
            
    def __imul__(self, scalar) -> PyGeVector2d:
        """Оператор *= (Vector *= Scalar)"""
        if isinstance(scalar, (int, float)):
            self.x *= scalar
            self.y *= scalar
            return self
        raise TypeError(f"Неподдерживаемый тип операнда {type(scalar)}")
        
    def __itruediv__(self, scalar) -> PyGeVector2d:
        """Оператор /= (Vector /= Scalar)"""
        if isinstance(scalar, (int, float)):
            if scalar == 0:
                raise ZeroDivisionError("Деление на ноль невозможно.")
            self.x /= scalar
            self.y /= scalar
            return self
        raise TypeError(f"Неподдерживаемый тип операнда {type(scalar)}")

    def length(self) -> float:
        """Возвращает длину (магнитуду) вектора"""
        return math.sqrt(self.lengthSqrd())
    
    def lengthSqrd(self) -> float:
        """Возвращает квадрат длины вектора"""
        # Можно использовать вместо length() для сравнения длин 2 векторов (быстрее length())
        return self.x**2 + self.y**2

    def normalize(self) -> PyGeVector2d:
        """Нормализует вектор (делает его единичным)"""
        len_val = self.length()
        if len_val == 0:
            raise ZeroDivisionError("Невозможно нормализовать нулевой вектор.")
        self.x /= len_val
        self.y /= len_val
        return self

    def normal(self) -> PyGeVector2d:
        """Возвращает новый нормализованный (единичный) вектор"""
        len_val = self.length()
        if len_val == 0:
            raise ZeroDivisionError("Невозможно получить нормаль от нулевого вектора.")
        return PyGeVector2d(self.x / len_val, self.y / len_val)
        
    def dotProduct(self, vector: PyGeVector2d) -> float:
        """Скалярное произведение векторов"""
        if isinstance(vector, PyGeVector2d):
            return (self.x * vector.x + 
                    self.y * vector.y)
        raise TypeError(f"Неподдерживаемый тип операнда {type(vector)}")

    def crossProduct(self, vector: PyGeVector2d) -> float:
        """Векторное произведение векторов"""
        if isinstance(vector, PyGeVector2d):
            return self.x * vector.y - self.y * vector.x
        raise TypeError(f"Неподдерживаемый тип операнда {type(vector)}")
        
    def angleTo(self, vector: PyGeVector2d) -> float:
        """Вычисляет угол между двумя векторами в радианах"""
        if isinstance(vector, PyGeVector2d):
            # cos(theta) = (A . B) / (|A| * |B|)
            dot = self.dotProduct(vector)
            len1 = self.length()
            len2 = vector.length()
            if len1 == 0 or len2 == 0:
                return 0.0 # Угол для нулевых векторов не определен
            # Ограничиваем значение в диапазоне [-1, 1] для безопасности acos при ошибках округления
            cosine_angle = max(-1.0, min(dot / (len1 * len2), 1.0))
            return math.acos(cosine_angle)
        raise TypeError(f"Неподдерживаемый тип операнда {type(vector)}")

    def isEqualTo(self, vector: PyGeVector2d, tolerance=1e-9) -> bool:
        """Проверяет равенство векторов с учетом допуска"""
        if isinstance(vector, PyGeVector2d):
            dx = abs(self.x - vector.x)
            dy = abs(self.y - vector.y)
            return dx <= tolerance and dy <= tolerance
        raise TypeError(f"Неподдерживаемый тип операнда {type(vector)}")

    def negate(self) -> PyGeVector2d:
        """Инвертирует вектор"""
        self.x = -self.x
        self.y = -self.y
        return self
    

    # def __repr__(self):
    #     return f"{self.__class__.__name__}(x={self.x}, y={self.y}, z={self.z})"
    def __str__(self):
        return f"{self.__class__.__name__}(x={self.x}, y={self.y}, z={self.z})"
    
    kIdentity:PyGeVector2d # Нулевой вектор
    kXaxis:PyGeVector2d # Единичный вектор X
    kYaxis:PyGeVector2d # Единичный вектор Y

PyGeVector2d.kIdentity  = PyGeVector2d(0.0, 0.0) # Нулевой вектор
PyGeVector2d.kXaxis     = PyGeVector2d(1.0, 0.0) # Единичный вектор X
PyGeVector2d.kYaxis     = PyGeVector2d(0.0, 1.0) # Единичный вектор Y
