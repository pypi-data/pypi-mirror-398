import sys
sys.path.insert(0, './src')

from src.teorver import *

def test_classical_probability():
    assert classical_probability(1, 2) == 0.5
    assert classical_probability(3, 4) == 0.75

def test_bernoulli_probability():
    # Вероятность 2 успеха в 4 испытаниях с p=0.5
    assert abs(bernoulli_probability(4, 2, 0.5) - 0.375) < 1e-6

def test_expected_value():
    # Ожидаемое значение: 0*0.3 + 1*0.7 = 0.7
    assert expected_value([0, 1], [0.3, 0.7]) == 0.7

def test_total_probability():
    # Полная вероятность: 0.3*0.2 + 0.7*0.5 = 0.06 + 0.35 = 0.41
    result = total_probability([0.3, 0.7], [0.2, 0.5])
    assert abs(result - 0.41) < 1e-6

def test_bayes_probability():
    # Формула Байеса для первой гипотезы
    result = bayes_probability(0, [0.3, 0.7], [0.2, 0.5])
    expected = (0.3 * 0.2) / 0.41  # 0.06 / 0.41
    assert abs(result - expected) < 1e-6

if __name__ == "__main__":
    test_classical_probability()
    test_bernoulli_probability()
    test_expected_value()
    test_total_probability()
    test_bayes_probability()
    print("Все тесты вероятности пройдены!")