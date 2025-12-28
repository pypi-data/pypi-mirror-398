import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mathutilspro.basic_operations import BasicOperations


class TestBasicOperations(unittest.TestCase):

    def test_add(self):
        self.assertEqual(BasicOperations.add(5, 3), 8)
        self.assertEqual(BasicOperations.add(-1, 1), 0)
        self.assertEqual(BasicOperations.add(0, 0), 0)

    def test_subtract(self):
        self.assertEqual(BasicOperations.subtract(10, 4), 6)
        self.assertEqual(BasicOperations.subtract(0, 5), -5)

    def test_multiply(self):
        self.assertEqual(BasicOperations.multiply(7, 6), 42)
        self.assertEqual(BasicOperations.multiply(-3, 4), -12)

    def test_divide(self):
        self.assertEqual(BasicOperations.divide(10, 2), 5)
        self.assertEqual(BasicOperations.divide(5, 2), 2.5)

        with self.assertRaises(ValueError):
            BasicOperations.divide(5, 0)

    def test_power(self):
        self.assertEqual(BasicOperations.power(2, 3), 8)
        self.assertEqual(BasicOperations.power(5, 0), 1)


if __name__ == '__main__':
    unittest.main()