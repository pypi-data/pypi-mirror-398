import math


class Vector:
    def __init__(self, data):

        if not isinstance(data, list):
            # Защита от дурака: если передали не список, пробуем преобразовать
            data = list(data)

        # Проверка, что внутри только числа
        if not all(isinstance(x, (int, float)) for x in data):
            raise TypeError("Вектор должен состоять только из чисел")

        self.data = data

    #Базовые методы Python

    def __len__(self):

        return len(self.data)

    def __getitem__(self, index):

        return self.data[index]

    def __setitem__(self, index, value):

        self.data[index] = value

    def __repr__(self):

        return f"Vector({self.data})"

    # Линейная алгебра встроенные методы

    def __add__(self, other):
        #Сложение векторов: v1 + v2
        if not isinstance(other, Vector):
            raise TypeError("Складывать можно только вектор с вектором")
        if len(self) != len(other):
            raise ValueError("Размерности векторов должны совпадать")

        # Поэлементное сложение
        new_data = [x + y for x, y in zip(self.data, other.data)]
        return Vector(new_data)

    def __sub__(self, other):
        #Вычитание векторов: v1 - v2
        if not isinstance(other, Vector):
            raise TypeError("Вычитать можно только вектор из вектора")
        if len(self) != len(other):
            raise ValueError("Размерности векторов должны совпадать")

        new_data = [x - y for x, y in zip(self.data, other.data)]
        return Vector(new_data)

    def __mul__(self, scalar):
        #Умножение вектора на число: v * 2
        if isinstance(scalar, (int, float)):
            new_data = [x * scalar for x in self.data]
            return Vector(new_data)
        else:
            raise TypeError("Вектор можно умножать только на число (скаляр)")

    def __rmul__(self, scalar):
        #Умножение числа на вектор (обратный порядок): 2 * v
        return self.__mul__(scalar)

    #Методы Линейной Алгебра

    def dot(self, other):

        if not isinstance(other, Vector):
            raise TypeError("Аргумент должен быть вектором")
        if len(self) != len(other):
            raise ValueError("Размерности векторов должны совпадать")

        return sum(x * y for x, y in zip(self.data, other.data))

    def norm(self):
        return math.sqrt(self.dot(self))

    def normalize(self):

        length = self.norm()
        if length == 0:
            raise ValueError("Нельзя нормализовать нулевой вектор")
        return self * (1.0 / length)