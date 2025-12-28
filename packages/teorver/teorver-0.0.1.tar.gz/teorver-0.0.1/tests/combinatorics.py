import sys
sys.path.insert(0, './src')  # Добавляем src в путь

from src.teorver import *

def test_factorial():
    assert factorial(5) == 120
    assert factorial(0) == 1

def test_permutations():
    assert permutations(4) == 24

def test_arrangements():
    assert arrangements(5, 2) == 20
    assert arrangements(5, 5) == 120

def test_combinations():
    assert combinations(5, 2) == 10
    assert combinations(5, 0) == 1

def test_arrangements_with_repetition():
    assert arrangements_with_repetition(3, 2) == 9

def test_combinations_with_repetition():
    assert combinations_with_repetition(3, 2) == 6

if __name__ == "__main__":
    test_factorial()
    test_permutations()
    test_arrangements()
    test_combinations()
    test_arrangements_with_repetition()
    test_combinations_with_repetition()
    print("Все тесты комбинаторики пройдены!")