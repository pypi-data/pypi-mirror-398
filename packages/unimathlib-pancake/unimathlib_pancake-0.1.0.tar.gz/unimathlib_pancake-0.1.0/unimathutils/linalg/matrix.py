from unimathutils.linalg.vector import Vector


class Matrix(Vector):
    def __init__(self, rows, cols, data=None):

        self.rows = rows
        self.cols = cols

        # Проверка размеров
        if data is None:
            data = [0.0] * (rows * cols)

        if len(data) != rows * cols:
            raise ValueError(f"Размер данных ({len(data)}) не совпадает с размером матрицы {rows}x{cols}")

        # Инициализируем родительский класс Vector
        # self.data доступен через методы Vector
        super().__init__(data)

    def __repr__(self):
        #вывод матрицы в консоль
        s = f"Matrix ({self.rows}x{self.cols}):\n"
        for i in range(self.rows):
            row_data = [self[i, j] for j in range(self.cols)]
            s += f"  {row_data}\n"
        return s

    def __getitem__(self, index):
        """
        Доступ к элементам.
        Поддерживает два вида индексов:
        1. m[i] -> возвращает элемент как в плоском векторе (редко нужно)
        2. m[row, col] -> возвращает элемент по координатам
        """
        if isinstance(index, tuple):
            row, col = index
            if 0 <= row < self.rows and 0 <= col < self.cols:
                # Формула перевода 2D координат в 1D индекс
                flat_index = row * self.cols + col
                return super().__getitem__(flat_index)
            else:
                raise IndexError("Индекс матрицы выходит за границы")
        else:
            return super().__getitem__(index)

    def __setitem__(self, index, value):
        """Запись элементов m[row, col] = value"""
        if isinstance(index, tuple):
            row, col = index
            flat_index = row * self.cols + col
            super().__setitem__(flat_index, value)
        else:
            super().__setitem__(index, value)


    def _check_dims(self, other):
        if not isinstance(other, Matrix):
            raise TypeError("Операция возможна только между матрицами")
        if self.rows != other.rows or self.cols != other.cols:
            raise ValueError(f"Размеры матриц не совпадают: ({self.rows}x{self.cols}) и ({other.rows}x{other.cols})")

    def __add__(self, other):
        self._check_dims(other)
        # Используем логику сложения из Vector (super)
        vector_result = super().__add__(other)
        # Оборачиваем результат обратно в Matrix
        return Matrix(self.rows, self.cols, vector_result.data)

    def __sub__(self, other):
        self._check_dims(other)
        vector_result = super().__sub__(other)
        return Matrix(self.rows, self.cols, vector_result.data)

    def __mul__(self, scalar):
        #Умножение матрицы на скаляр (число)
        vector_result = super().__mul__(scalar)
        return Matrix(self.rows, self.cols, vector_result.data)

    #Матричное умножение

    def __matmul__(self, other):
        #Оператор @ для матричного умножения: C = A @ B

        if isinstance(other, Vector) and not isinstance(other, Matrix):
            # Умножение Матрица @ Вектор (возвращает Вектор)
            if self.cols != len(other):
                raise ValueError("Число столбцов матрицы должно совпадать с длиной вектора")

            result_data = []
            for i in range(self.rows):
                # Скалярное произведение i-й строки матрицы на вектор
                row_val = 0
                for k in range(self.cols):
                    row_val += self[i, k] * other[k]
                result_data.append(row_val)
            return Vector(result_data)

        elif isinstance(other, Matrix):
            # Умножение Матрица Матрица (возвращает Матрицу)
            if self.cols != other.rows:
                raise ValueError(f"Нельзя умножить матрицу {self.rows}x{self.cols} на {other.rows}x{other.cols}")

            new_data = []
            for i in range(self.rows):
                for j in range(other.cols):
                    dot_val = 0
                    for k in range(self.cols):
                        dot_val += self[i, k] * other[k, j]
                    new_data.append(dot_val)

            return Matrix(self.rows, other.cols, new_data)

        else:
            raise TypeError("Матрицу можно умножать только на Матрицу или Вектор")
