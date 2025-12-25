from __future__ import annotations
from .Vector import *
from .Points import *
import numpy as np
import math

class PyGeMatrix3d:
    """Матрица трансформации 4x4."""

    def __init__(self, matrix_data: PyGeMatrix3d|np.ndarray|None = None):
        # По умолчанию создаем единичную матрицу 4x4 (Identity Matrix)
        if matrix_data is None:
            self.matrix:np.ndarray = np.eye(4, dtype=float)
        elif isinstance(matrix_data, np.ndarray) and matrix_data.shape == (4, 4):
            self.matrix:np.ndarray = matrix_data
        elif isinstance(matrix_data, PyGeMatrix3d):
            self.matrix:np.ndarray = matrix_data.matrix.copy()
        else:
            raise ValueError("Матрица должна быть numpy-массивом 4x4 или PyGeMatrix3d")

    # def __repr__(self):
    #     return f"PyGeMatrix3d(\n{self.matrix}\n)"
    def __str__(self):
        return f"{self.__class__.__name__}(\n{self.matrix}\n)"

    
    @staticmethod
    def translation(vector: PyGeVector3d) -> PyGeMatrix3d:
        """Создает матрицу сдвига (трансляции) по вектору"""
        m = np.eye(4)
        m[:3, 3] = [vector.x, vector.y, vector.z]
        return PyGeMatrix3d(m)

    @staticmethod
    def rotation(angle_rad: float, axis: PyGeVector3d, center: PyGePoint3d = None) -> PyGeMatrix3d:
        """
        Создает матрицу поворота вокруг произвольной оси на заданный угол.
        Если указан center, вращение происходит относительно этой точки.
        """
        axis_vec = np.array([axis.x, axis.y, axis.z])
        # Убедимся, что ось нормализована
        axis_norm = axis_vec / np.linalg.norm(axis_vec)
        ux, uy, uz = axis_norm

        cos_theta = math.cos(angle_rad)
        sin_theta = math.sin(angle_rad)
        one_minus_cos = 1 - cos_theta

        # Формула матрицы вращения Родригеса для произвольной оси:
        R = np.array([
            [cos_theta + ux**2 * one_minus_cos,     ux*uy*one_minus_cos - uz*sin_theta,     ux*uz*one_minus_cos + uy*sin_theta, 0],
            [uy*ux*one_minus_cos + uz*sin_theta,    cos_theta + uy**2 * one_minus_cos,      uy*uz*one_minus_cos - ux*sin_theta, 0],
            [uz*ux*one_minus_cos - uy*sin_theta,    uz*uy*one_minus_cos + ux*sin_theta,     cos_theta + uz**2 * one_minus_cos,  0],
            [0, 0, 0, 1]
        ])
        
        M_rotate = PyGeMatrix3d(R)

        if center is None:
            # Поворот относительно начала координат
            return M_rotate
        else:
            # Поворот относительно произвольного центра (P - C, Rotate, P + C)
            C = np.array([center.x, center.y, center.z])
            T1 = PyGeMatrix3d.translation(PyGeVector3d(-C))
            T2 = PyGeMatrix3d.translation(PyGeVector3d(C))
            
            # Комбинируем матрицы: T2 * R * T1
            combined_matrix = T2.matrix @ M_rotate.matrix @ T1.matrix
            return PyGeMatrix3d(combined_matrix)


    @staticmethod
    def scaling(scale_factor: float, center: PyGePoint3d = None) -> PyGeMatrix3d:
        """Создает матрицу масштабирования. Если указан center, масштабирование происходит относительно этой точки."""

        # 1. Сначала создаем базовую матрицу масштабирования относительно начала координат
        m_scale_base = np.eye(4)
        m_scale_base[0, 0] = scale_factor
        m_scale_base[1, 1] = scale_factor
        m_scale_base[2, 2] = scale_factor
        
        # Оборачиваем ее в объект PyGeMatrix3d
        S = PyGeMatrix3d(m_scale_base)
        
        if center is None:
            # Если центр не указан, возвращаем S
            return S
        else:
            # Если центр указан, комбинируем матрицы сдвига
            C = np.array([center.x, center.y, center.z])
            
            # T1: Сдвиг центра в начало координат
            T1 = PyGeMatrix3d.translation(PyGeVector3d(-C[0], -C[1], -C[2]))
            
            # T2: Обратный сдвиг из начала координат
            T2 = PyGeMatrix3d.translation(PyGeVector3d(C[0], C[1], C[2]))
            
            # Комбинируем матрицы: T2 * S * T1 (помните о порядке умножения матриц!)
            combined_matrix = T2.matrix @ S.matrix @ T1.matrix
            return PyGeMatrix3d(combined_matrix)

    @staticmethod
    def mirroring(plane_origin: PyGePoint3d, plane_normal: PyGeVector3d) -> PyGeMatrix3d:
        """
        Создает матрицу отражения относительно заданной плоскости.
        plane_origin: PyGePoint3d - точка на плоскости.
        plane_normal: PyGeVector3d - вектор нормали к плоскости.
        """
        
        # 1. Нормализуем вектор
        n_vec = np.array([plane_normal.x, plane_normal.y, plane_normal.z])
        n_vec = n_vec / np.linalg.norm(n_vec)
        Nx, Ny, Nz = n_vec
        
        # 2. Базовая матрица отражения (относительно плоскости через начало координат)
        # Формула Родригеса для отражения: I - 2*N*N^T
        M_base_3x3 = np.array([
            [1 - 2*Nx**2,   -2*Nx*Ny,       -2*Nx*Nz],
            [-2*Nx*Ny,      1 - 2*Ny**2,    -2*Ny*Nz],
            [-2*Nx*Nz,      -2*Ny*Nz,       1 - 2*Nz**2]
        ])

        # Преобразуем в гомогенную матрицу 4x4
        M_mirror_base = np.eye(4)
        M_mirror_base[:3, :3] = M_base_3x3
        
        M_mirror = PyGeMatrix3d(M_mirror_base)

        # 3. Комбинация сдвигов, если плоскость не проходит через начало координат
        if plane_origin.x != 0 or plane_origin.y != 0 or plane_origin.z != 0:
            # T1: Сдвигаем начало координат на точку плоскости
            T1 = PyGeMatrix3d.translation(PyGeVector3d(-plane_origin.x, -plane_origin.y, -plane_origin.z))
            # T2: Обратный сдвиг
            T2 = PyGeMatrix3d.translation(PyGeVector3d(plane_origin.x, plane_origin.y, plane_origin.z))
            
            # M = T2 @ M_mirror @ T1
            combined_matrix = T2.matrix @ M_mirror.matrix @ T1.matrix
            return PyGeMatrix3d(combined_matrix)
        
        return M_mirror
    
    @staticmethod
    def projection(plane_origin: PyGePoint3d, plane_normal: PyGeVector3d) -> PyGeMatrix3d:
        """
        Создает матрицу ортогональной проекции на заданную плоскость.
        plane_origin: PyGePoint3d - точка на плоскости.
        plane_normal: PyGeVector3d - вектор нормали к плоскости.
        """
        
        # 1. Нормализуем вектор плоскости
        n_vec = np.array([plane_normal.x, plane_normal.y, plane_normal.z])
        n_vec = n_vec / np.linalg.norm(n_vec)
        Nx, Ny, Nz = n_vec

        # 2. Базовая матрица проекции (формула: I - N*N^T) (3x3)
        M_base_3x3 = np.array([
            [1 - Nx**2,   -Nx*Ny,    -Nx*Nz],
            [-Nx*Ny,    1 - Ny**2,   -Ny*Nz],
            [-Nx*Nz,    -Ny*Nz,    1 - Nz**2]
        ])

        # 3. Преобразуем в гомогенную матрицу 4x4
        M_proj_base = np.eye(4)
        M_proj_base[:3, :3] = M_base_3x3
        
        M_proj = PyGeMatrix3d(M_proj_base)

        # 4. Комбинация сдвигов, если плоскость не проходит через начало координат
        if plane_origin.x != 0 or plane_origin.y != 0 or plane_origin.z != 0:
            # T1: Сдвигаем начало координат на точку плоскости
            T1 = PyGeMatrix3d.translation(PyGeVector3d(-plane_origin.x, -plane_origin.y, -plane_origin.z))
            # T2: Обратный сдвиг
            T2 = PyGeMatrix3d.translation(PyGeVector3d(plane_origin.x, plane_origin.y, plane_origin.z))
            
            # M = T2 @ M_proj @ T1
            combined_matrix = T2.matrix @ M_proj.matrix @ T1.matrix
            return PyGeMatrix3d(combined_matrix)
        
        return M_proj

    def to_array(self): return np.array(self.matrix, dtype=np.float64)

    def __mul__(self, other: PyGeMatrix3d|int|float) -> PyGeMatrix3d:
        """Умножение матриц (Matrix *= Matrix и Matrix *= Scalar)"""
        if isinstance(other, PyGeMatrix3d):
            # Матричное умножение NumPy
            result_matrix = self.matrix @ other.matrix
            return PyGeMatrix3d(result_matrix)
        elif isinstance(other, (int, float)):
            result_matrix = self.matrix * other
            return PyGeMatrix3d(result_matrix)
        raise TypeError(f"Неподдерживаемый тип операнда {type(other)}")

    def __imul__(self, other: PyGeMatrix3d|int|float) -> PyGeMatrix3d:
        """Умножение матриц (Matrix *= Matrix и Matrix *= Scalar)"""
        if isinstance(other, PyGeMatrix3d):
            # Матричное умножение NumPy
            self.matrix = self.matrix @ other.matrix
            return self
        elif isinstance(other, (int, float)):
            self.matrix = self.matrix * other
            return self
        raise TypeError(f"Неподдерживаемый тип операнда {type(other)}")
    
    def invert(self):
        """Инвертирует текущую матрицу"""
        self.matrix = np.linalg.inv(self.matrix)
        return self

    def inverse(self):
        """Возвращает новую инвертированную матрицу"""
        inverted_matrix = np.linalg.inv(self.matrix)
        return PyGeMatrix3d(inverted_matrix)

    def transposeIt(self) -> PyGeMatrix3d:
        """Транспонирует текущую матрицу"""
        self.matrix = self.matrix.T
        return self

    def transpose(self) -> PyGeMatrix3d:
        """Возвращает транспонированную матрицу"""
        return PyGeMatrix3d(self.matrix.T)

    def __call__(self):
        """Возвращает VARIANT для методов CDispatch"""
        return Variant(self.matrix,VT.ARRAY_DOUBLE).to_variant()




class PyGeMatrix2d:
    """Матрица трансформации 3x3."""

    def __init__(self, matrix_data: PyGeMatrix3d|np.ndarray|None = None):
        # По умолчанию создаем единичную матрицу 3x3 (Identity Matrix)
        if matrix_data is None:
            self.matrix:np.ndarray = np.eye(3, dtype=float)
        elif isinstance(matrix_data, np.ndarray) and matrix_data.shape == (3, 3):
            self.matrix:np.ndarray = matrix_data
        elif isinstance(matrix_data, PyGeMatrix3d):
            self.matrix:np.ndarray = matrix_data.matrix.copy()
        else:
            raise ValueError("Матрица должна быть numpy-массивом 3x3 или PyGeMatrix2d")

    def __str__(self):
        return f"{self.__class__.__name__}(\n{self.matrix}\n)"

    
    @staticmethod
    def translation(vector: PyGeVector2d) -> PyGeMatrix2d:
        """Создает матрицу сдвига (трансляции) по вектору PyGeVector2d"""
        m = np.eye(3)
        m[0, 2] = vector.x
        m[1, 2] = vector.y
        return PyGeMatrix2d(m)

    @staticmethod
    def rotation(angle_rad: float, center: PyGePoint2d = None) -> PyGeMatrix2d:
        """
        Создает матрицу поворота на заданный угол (в радианах) вокруг точки.
        В 2D вращение всегда происходит вокруг оси Z.
        """
        cos_theta = math.cos(angle_rad)
        sin_theta = math.sin(angle_rad)
        
        # Базовая матрица поворота 3x3 относительно начала координат
        m_rotate_base = np.array([
            [cos_theta, -sin_theta, 0],
            [sin_theta, cos_theta,  0],
            [0,         0,          1]
        ])
        
        M_rotate = PyGeMatrix2d(m_rotate_base)

        if center is None:
            # Поворот относительно начала координат
            return M_rotate
        else:
            # Поворот относительно произвольного центра (комбинация сдвигов)
            # T2 * R * T1
            T1 = PyGeMatrix2d.translation(PyGeVector2d(-center.x, -center.y))
            T2 = PyGeMatrix2d.translation(PyGeVector2d(center.x, center.y))
            
            # Комбинируем матрицы: T2 @ M_rotate @ T1
            combined_matrix = T2.matrix @ M_rotate.matrix @ T1.matrix
            return PyGeMatrix2d(combined_matrix)

    @staticmethod
    def scaling(scale_factor: float, center: PyGePoint2d = None) -> PyGeMatrix2d:
        """Создает матрицу масштабирования. Если указан center, масштабирование происходит относительно этой точки."""

        # 1. Сначала создаем базовую матрицу масштабирования относительно начала координат
        m_scale_base = np.eye(4)
        m_scale_base[0, 0] = scale_factor
        m_scale_base[1, 1] = scale_factor
        
        # Оборачиваем ее в объект PyGeMatrix2d
        S = PyGeMatrix2d(m_scale_base)
        
        if center is None:
            # Если центр не указан, возвращаем S
            return S
        else:
            # Комбинируем матрицы сдвига для масштабирования относительно центра
            T1 = PyGeMatrix2d.translation(PyGeVector2d(-center.x, -center.y))
            T2 = PyGeMatrix2d.translation(PyGeVector2d(center.x, center.y))
            
            # Комбинируем матрицы: T2 @ S @ T1
            combined_matrix = T2.matrix @ S.matrix @ T1.matrix
            return PyGeMatrix2d(combined_matrix)


    @staticmethod
    def mirroring(line_origin: PyGePoint2d, line_normal: PyGeVector2d) -> PyGeMatrix2d:
        """
        Создает матрицу отражения относительно заданной прямой (линии) в 2D.
        line_origin: PyGePoint2d - точка на прямой.
        line_normal: PyGeVector2d - вектор нормали к прямой.
        """
        
        # 1. Нормализуем вектор на всякий случай
        n_vec = np.array([line_normal.x, line_normal.y])
        n_vec = n_vec / np.linalg.norm(n_vec)
        Nx, Ny = n_vec

        # 2. Базовая матрица отражения 2x2 (относительно линии через начало координат)
        M_base_2x2 = np.array([
            [1 - 2*Nx**2,   -2*Nx*Ny],
            [-2*Nx*Ny,      1 - 2*Ny**2]
        ])

        # Преобразуем в гомогенную матрицу 3x3
        M_mirror_base = np.eye(3)
        M_mirror_base[:2, :2] = M_base_2x2
        
        M_mirror = PyGeMatrix2d(M_mirror_base)

        # 3. Комбинация сдвигов, если линия не проходит через начало координат
        if line_origin.x != 0 or line_origin.y != 0:
            T1 = PyGeMatrix2d.translation(PyGeVector2d(-line_origin.x, -line_origin.y))
            T2 = PyGeMatrix2d.translation(PyGeVector2d(line_origin.x, line_origin.y))
            
            # M = T2 @ M_mirror @ T1
            combined_matrix = T2.matrix @ M_mirror.matrix @ T1.matrix
            return PyGeMatrix2d(combined_matrix)
            
        return M_mirror

    @staticmethod
    def projection(line_origin: PyGePoint2d, line_normal: PyGeVector2d) -> PyGeMatrix2d:
        """
        Создает матрицу ортогональной проекции на заданную прямую (линию) в 2D.
        line_origin: PyGePoint2d - точка на прямой.
        line_normal: PyGeVector2d - вектор нормали к прямой.
        """
        
        # 1. Нормализуем вектор прямой
        n_vec = np.array([line_normal.x, line_normal.y])
        n_vec = n_vec / np.linalg.norm(n_vec)
        Nx, Ny = n_vec

        # 2. Базовая матрица проекции (формула: I - N*N^T) (2x2)
        M_base_2x2 = np.array([
            [1 - Nx**2,   -Nx*Ny],
            [-Nx*Ny,    1 - Ny**2]
        ])

        # 3. Преобразуем в гомогенную матрицу 3x3
        M_proj_base = np.eye(3)
        M_proj_base[:2, :2] = M_base_2x2
        
        M_proj = PyGeMatrix2d(M_proj_base)

        # 4. Комбинация сдвигов, если прямая не проходит через начало координат
        if line_origin.x != 0 or line_origin.y != 0:
            T1 = PyGeMatrix2d.translation(PyGeVector2d(-line_origin.x, -line_origin.y))
            T2 = PyGeMatrix2d.translation(PyGeVector2d(line_origin.x, line_origin.y))
            
            # M = T2 @ M_proj @ T1
            combined_matrix = T2.matrix @ M_proj.matrix @ T1.matrix
            return PyGeMatrix2d(combined_matrix)
        
        return M_proj

    def __mul__(self, other: PyGeMatrix2d|int|float) -> PyGeMatrix2d:
        """Умножение матриц (Matrix *= Matrix и Matrix *= Scalar)"""
        if isinstance(other, PyGeMatrix2d):
            # Матричное умножение NumPy
            result_matrix = self.matrix @ other.matrix
            return PyGeMatrix2d(result_matrix)
        elif isinstance(other, (int, float)):
            result_matrix = self.matrix * other
            return PyGeMatrix2d(result_matrix)
        raise TypeError(f"Неподдерживаемый тип операнда {type(other)}")

    def __imul__(self, other: PyGeMatrix2d|int|float) -> PyGeMatrix2d:
        """Умножение матриц (Matrix *= Matrix и Matrix *= Scalar)"""
        if isinstance(other, PyGeMatrix2d):
            # Матричное умножение NumPy
            self.matrix = self.matrix @ other.matrix
            return self
        elif isinstance(other, (int, float)):
            self.matrix = self.matrix * other
            return self
        raise TypeError(f"Неподдерживаемый тип операнда {type(other)}")
    
    def invert(self) -> None:
        """Инвертирует текущую матрицу"""
        self.matrix = np.linalg.inv(self.matrix)
        # return self

    def inverse(self) -> PyGeMatrix2d:
        """Возвращает новую инвертированную матрицу"""
        inverted_matrix = np.linalg.inv(self.matrix)
        return PyGeMatrix2d(inverted_matrix)
    
    def transposeIt(self) -> None:
        """Транспонирует текущую матрицу"""
        self.matrix = self.matrix.T
        # return self

    def transpose(self) -> PyGeMatrix2d:
        """Возвращает транспонированную матрицу"""
        return PyGeMatrix2d(self.matrix.T)

    def __call__(self):
        """Возвращает Variant для методов CDispatch"""
        return Variant(self.matrix,VT.ARRAY_DOUBLE).to_variant()