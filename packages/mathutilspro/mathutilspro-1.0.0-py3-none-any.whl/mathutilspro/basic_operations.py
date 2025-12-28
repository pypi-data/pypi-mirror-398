class BasicOperations:
    """Класс для базовых математических операций"""

    @staticmethod
    def add(a, b):
        """Сложение двух чисел"""
        return a + b

    @staticmethod
    def subtract(a, b):
        """Вычитание"""
        return a - b

    @staticmethod
    def multiply(a, b):
        """Умножение"""
        return a * b

    @staticmethod
    def divide(a, b):
        """Деление с проверкой на ноль"""
        if b == 0:
            raise ValueError("Деление на ноль невозможно")
        return a / b

    @staticmethod
    def power(base, exponent):
        """Возведение в степень"""
        return base ** exponent