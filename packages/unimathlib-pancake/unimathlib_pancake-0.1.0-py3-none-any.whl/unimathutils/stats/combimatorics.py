import math


def factorial(n: int) -> int:

    ###Факториал числа n

    if not isinstance(n, int):
        raise TypeError("Факториал определён только для целых чисел")
    if n < 0:
        raise ValueError("Факториал определён только для n >= 0")

    return math.factorial(n)


def combinations(n: int, k: int) -> int:
    #Сочетания без повторений:
    if not (0 <= k <= n):
        raise ValueError("Должно выполняться 0 <= k <= n")

    return factorial(n) // (factorial(k) * factorial(n - k))


def permutations(n: int) -> int:

    #Перестановки:

    return factorial(n)


def arrangements(n: int, k: int) -> int:

#Размещения без повторений:

    if not (0 <= k <= n):
        raise ValueError("Должно выполняться 0 <= k <= n")

    return factorial(n) // factorial(n - k)


def arrangements_with_repetition(n: int, k: int) -> int:

    #Размещения с повторениями:

    if n < 0 or k < 0:
        raise ValueError("n и k должны быть неотрицательными")

    return n ** k


def binomial_probability(n: int, k: int, p: float) -> float:

    #Биномиальное распределение:

    if not (0 <= p <= 1):
        raise ValueError("Вероятность p должна быть в диапазоне [0, 1]")
    if not (0 <= k <= n):
        raise ValueError("Должно выполняться 0 <= k <= n")

    return combinations(n, k) * (p ** k) * ((1 - p) ** (n - k))
