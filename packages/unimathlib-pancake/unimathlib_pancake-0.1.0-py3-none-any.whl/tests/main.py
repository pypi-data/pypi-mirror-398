import unittest
import math
import sys
import os

# Добавляем корень проекта в sys.path, чтобы импорт работал
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from unimathutils.linalg.vector import Vector  # импорт вашего класса


class TestVector(unittest.TestCase):

    def setUp(self):
        #вектор для тестов
        self.v1 = Vector([1, 2, 3])
        self.v2 = Vector([4, 5, 6])
        self.v_float = Vector([1.5, 2.5])

    # Тест инициализации
    def test_init(self):
        # Проверка длины
        self.assertEqual(len(self.v1), 3)
        # Проверка доступа по индексу
        self.assertEqual(self.v1[0], 1)
        # Проверка защиты от неправильного типа
        with self.assertRaises(TypeError):
            Vector(["a", "b"])

    # Тест арифметики
    def test_add_sub_mul(self):
        # Сложение
        v_sum = self.v1 + self.v2
        self.assertEqual(v_sum.data, [5, 7, 9])
        # Вычитание
        v_sub = self.v2 - self.v1
        self.assertEqual(v_sub.data, [3, 3, 3])
        # Умножение на скаляр
