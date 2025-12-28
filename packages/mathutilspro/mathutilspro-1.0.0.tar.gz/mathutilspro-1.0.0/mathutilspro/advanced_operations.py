import math


class AdvancedOperations:
    """Класс для продвинутых математических операций"""

    @staticmethod
    def factorial(n):
        """Вычисление факториала"""
        if n < 0:
            raise ValueError("Факториал отрицательного числа не определен")
        if n == 0:
            return 1
        return math.prod(range(1, n + 1))

    @staticmethod
    def fibonacci(n):
        """Вычисление n-го числа Фибоначчи"""
        if n < 0:
            raise ValueError("Индекс должен быть неотрицательным")
        if n == 0:
            return 0
        elif n == 1:
            return 1

        a, b = 0, 1
        for _ in range(2, n + 1):
            a, b = b, a + b
        return b

    @staticmethod
    def is_prime(n):
        """Проверка числа на простоту"""
        if n < 2:
            return False
        if n == 2:
            return True
        if n % 2 == 0:
            return False

        for i in range(3, int(math.sqrt(n)) + 1, 2):
            if n % i == 0:
                return False
        return True

    @staticmethod
    def gcd(a, b):
        """Наибольший общий делитель"""
        while b:
            a, b = b, a % b
        return abs(a)