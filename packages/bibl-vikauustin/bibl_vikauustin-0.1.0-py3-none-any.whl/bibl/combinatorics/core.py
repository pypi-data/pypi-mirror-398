def factorial(n: int) -> int:
    """Вычисление факториала числа n"""
    if n < 0:
        raise ValueError("Факториал определен только для неотрицательных чисел")
    if n == 0:
        return 1
    result = 1
    for i in range(1, n + 1):
        result *= i
    return result

def combinations(n: int, k: int) -> int:
    """Число сочетаний из n по k: C(n, k) = n! / (k! * (n-k)!)"""
    if k < 0 or k > n:
        return 0
    return factorial(n) // (factorial(k) * factorial(n - k))

def permutations(n: int, k: int) -> int:
    """Число размещений из n по k: A(n, k) = n! / (n-k)!"""
    if k < 0 or k > n:
        return 0
    return factorial(n) // factorial(n - k)

def generate_combinations(elements, k):
    """Генератор всех комбинаций из элементов по k"""
    from itertools import combinations
    return combinations(elements, k)

def generate_permutations(elements, k):
    """Генератор всех перестановок из элементов по k"""
    from itertools import permutations
    return permutations(elements, k)