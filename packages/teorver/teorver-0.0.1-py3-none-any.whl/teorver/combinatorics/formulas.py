import math

def factorial(n: int) -> int:
    if n < 0:
        raise ValueError("Факториал определён только для n >= 0")
    return math.factorial(n)


def permutations(n: int) -> int:
    return factorial(n)


def arrangements(n: int, k: int) -> int:
    if k > n or k < 0:
        raise ValueError("Должно быть 0 <= k <= n")
    return factorial(n) // factorial(n - k)


def combinations(n: int, k: int) -> int:
    if k > n or k < 0:
        raise ValueError("Должно быть 0 <= k <= n")
    return factorial(n) // (factorial(k) * factorial(n - k))


def arrangements_with_repetition(n: int, k: int) -> int:
    if n <= 0 or k < 0:
        raise ValueError("Должно быть n > 0 и k >= 0")
    return n ** k


def combinations_with_repetition(n: int, k: int) -> int:
    if n <= 0 or k < 0:
        raise ValueError("Должно быть n > 0 и k >= 0")
    return combinations(n + k - 1, k)