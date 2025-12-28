import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mathutilspro.advanced_operations import AdvancedOperations


class TestAdvancedOperations(unittest.TestCase):

    def test_factorial(self):
        self.assertEqual(AdvancedOperations.factorial(0), 1)
        self.assertEqual(AdvancedOperations.factorial(1), 1)
        self.assertEqual(AdvancedOperations.factorial(5), 120)

        with self.assertRaises(ValueError):
            AdvancedOperations.factorial(-1)

    def test_fibonacci(self):
        self.assertEqual(AdvancedOperations.fibonacci(0), 0)
        self.assertEqual(AdvancedOperations.fibonacci(1), 1)
        self.assertEqual(AdvancedOperations.fibonacci(5), 5)
        self.assertEqual(AdvancedOperations.fibonacci(10), 55)

    def test_is_prime(self):
        self.assertTrue(AdvancedOperations.is_prime(2))
        self.assertTrue(AdvancedOperations.is_prime(17))
        self.assertFalse(AdvancedOperations.is_prime(1))
        self.assertFalse(AdvancedOperations.is_prime(4))
        self.assertFalse(AdvancedOperations.is_prime(9))

    def test_gcd(self):
        self.assertEqual(AdvancedOperations.gcd(54, 24), 6)
        self.assertEqual(AdvancedOperations.gcd(17, 13), 1)
        self.assertEqual(AdvancedOperations.gcd(0, 5), 5)
        self.assertEqual(AdvancedOperations.gcd(10, 0), 10)


if __name__ == '__main__':
    unittest.main()