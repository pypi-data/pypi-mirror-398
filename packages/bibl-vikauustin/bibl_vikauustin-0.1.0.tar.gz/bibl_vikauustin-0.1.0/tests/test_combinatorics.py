import unittest
from bibl.combinatorics import (
    factorial, combinations, permutations,
    generate_combinations, generate_permutations
)

class TestCombinatorics(unittest.TestCase):
    
    def test_factorial(self):
        self.assertEqual(factorial(0), 1)
        self.assertEqual(factorial(1), 1)
        self.assertEqual(factorial(5), 120)
        self.assertEqual(factorial(6), 720)
        
    def test_factorial_negative(self):
        with self.assertRaises(ValueError):
            factorial(-1)
    
    def test_combinations(self):
        self.assertEqual(combinations(5, 2), 10)
        self.assertEqual(combinations(6, 3), 20)
        self.assertEqual(combinations(5, 5), 1)
        self.assertEqual(combinations(5, 6), 0)
        
    def test_permutations(self):
        self.assertEqual(permutations(5, 2), 20)
        self.assertEqual(permutations(6, 3), 120)
        self.assertEqual(permutations(5, 0), 1)
        
    def test_generate_combinations(self):
        elements = ['a', 'b', 'c']
        combos = list(generate_combinations(elements, 2))
        expected = [('a', 'b'), ('a', 'c'), ('b', 'c')]
        self.assertEqual(combos, expected)
        
    def test_generate_permutations(self):
        elements = ['a', 'b']
        perms = list(generate_permutations(elements, 2))
        expected = [('a', 'b'), ('b', 'a')]
        self.assertEqual(perms, expected)

if __name__ == '__main__':
    unittest.main()