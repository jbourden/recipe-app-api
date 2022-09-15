from django.test import SimpleTestCase
from app import calc

class CalcTests(SimpleTestCase):
    def test_add(self):
        res = calc.add(5,6)
        self.assertEqual(res, 11)

    def test_subtract(self):
        res = calc.subtract(10,10)
        self.assertEqual(res, 0)

    def test_multiply(self):
        res = calc.multiply(15, 10)
        self.assertEqual(res, 150)

    def test_divide(self):
        res = calc.divide(15, 5)
        self.assertEqual(res, 3)
