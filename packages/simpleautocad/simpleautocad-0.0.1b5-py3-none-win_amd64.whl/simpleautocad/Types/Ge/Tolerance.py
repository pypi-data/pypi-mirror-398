# class PyGeTol:
#     """
#     Допуски для линейных и угловых измерений.
#     """
#     # Допуск по умолчанию для линейных/пространственных сравнений
#     # Стандартное значение 1e-9
#     kEps: float = 1e-9 
    
#     # Допуск для сравнения углов (в радианах)
#     kAngEps: float = 1e-12

#     # AcGeTol.kEqualPoint - допуск для точек
#     kEqualPoint: float = kEps
#     # AcGeTol.kEqualVector - допуск для векторов (для проверки на равенство)
#     kEqualVector: float = kEps
#     # AcGeTol.kZeroVector - допуск для проверки, является ли длина вектора нулевой
#     kZeroVector: float = 1e-10 

# geTol = PyGeTol()