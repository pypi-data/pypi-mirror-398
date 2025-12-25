import unittest
from bibl.diffeq import euler_method, second_order_to_system

class TestDiffEq(unittest.TestCase):
    
    def test_euler_method_simple(self):
        """Тест для уравнения y' = 1, y(0) = 0"""
        def f(t, y):
            return 1
            
        t_vals, y_vals = euler_method(f, y0=0, t_range=(0, 1), n=10)
        
        # Проверяем количество точек
        self.assertEqual(len(t_vals), 11)
        self.assertEqual(len(y_vals), 11)
        
        # Проверяем конечное значение (должно быть примерно 1)
        self.assertAlmostEqual(y_vals[-1], 1.0, places=2)
        
    def test_euler_method_exponential(self):
        """Тест для уравнения y' = y, y(0) = 1"""
        def f(t, y):
            return y
            
        t_vals, y_vals = euler_method(f, y0=1, t_range=(0, 1), n=100)
        
        # При t=1 решение должно быть примерно e ≈ 2.718
        self.assertAlmostEqual(y_vals[-1], 2.718, delta=0.1)
    
    def test_second_order_to_system(self):
        """Тест для уравнения y'' = -y (гармонический осциллятор)"""
        def f(t, y, v):
            return -y  # y'' = -y
            
        t_vals, y_vals, v_vals = second_order_to_system(
            f, y0=0, dy0=1, t_range=(0, 6.28), n=100
        )
        
        # Проверяем размеры массивов
        self.assertEqual(len(t_vals), 101)
        self.assertEqual(len(y_vals), 101)
        self.assertEqual(len(v_vals), 101)
        
        # Проверяем начальные условия
        self.assertEqual(y_vals[0], 0)
        self.assertEqual(v_vals[0], 1)

if __name__ == '__main__':
    unittest.main()